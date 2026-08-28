"""
Inference Evaluator Engine — RF + CNN Ensemble.

Loads trained RF classifier/regressor and CNN model, predicts quality scores,
defect probabilities, issues with confidence and severity, natural language explanations,
and tree-agreement uncertainty estimation.
"""

import os
import json
import joblib
import logging
import numpy as np

from backend.app.ml.cnn_model import CNNQualityClassifier

logger = logging.getLogger(__name__)


class QualityEvaluator:
    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../models_store/model.joblib")
            )

        self.model_path = model_path
        self.classifier = None
        self.regressor = None
        self.classes = []
        self.metrics_info = {}
        self.is_loaded = False
        
        self.load_model()
        self.cnn = CNNQualityClassifier()

    def load_model(self):
        """Loads serialized RF model bundle and evaluation metrics."""
        if os.path.exists(self.model_path):
            try:
                bundle = joblib.load(self.model_path)
                self.classifier = bundle["classifier"]
                self.regressor = bundle["regressor"]
                self.classes = bundle["classes"]
                self.is_loaded = True

                metrics_file = os.path.join(os.path.dirname(self.model_path), "metrics.json")
                if os.path.exists(metrics_file):
                    with open(metrics_file, "r") as f:
                        self.metrics_info = json.load(f)

                logger.info(
                    f"RF model loaded from {self.model_path} "
                    f"(version={self.metrics_info.get('model_version', 'unknown')})"
                )
            except Exception as e:
                logger.error(f"Failed to load RF model: {e}")
                self.is_loaded = False
        else:
            logger.warning(f"RF model not found at {self.model_path}")

    def evaluate(self, feature_dict: dict, corruption_info: dict = None, img_bgr: np.ndarray = None) -> dict:
        """
        Evaluates image quality using RF + CNN ensemble and calculates tree agreement uncertainty.
        """
        feat_vector = feature_dict["feature_vector"]
        raw_metrics = feature_dict["raw_metrics"]
        uncertainty = None

        # 1. Corruption check
        if corruption_info and corruption_info.get("is_corrupt", False):
            return {
                "quality_score": 0.0,
                "quality_label": "DEFECTIVE",
                "issues": [{
                    "type": "corruption",
                    "severity": "high",
                    "confidence": 0.99,
                    "description": corruption_info.get("corruption_reason", "Severe file corruption")
                }],
                "explanation": "Image analysis failed due to severe structural corruption.",
                "predicted_class": "DEFECTIVE",
                "ml_confidence": 0.99,
                "cnn_prediction": None,
                "uncertainty": None,
            }

        # 2. Rule-based issue detection
        issues = []

        if raw_metrics["laplacian_variance"] < 80.0:
            sev = "high" if raw_metrics["laplacian_variance"] < 35.0 else "medium"
            conf = min(0.99, max(0.65, round(1.0 - raw_metrics["laplacian_variance"] / 90.0, 2)))
            issues.append({
                "type": "blur", "severity": sev, "confidence": conf,
                "description": f"Insufficient sharpness (Laplacian variance: {raw_metrics['laplacian_variance']})"
            })

        if raw_metrics["underexpose_ratio"] > 0.25 or raw_metrics["mean_brightness"] < 50.0:
            sev = "high" if raw_metrics["mean_brightness"] < 25.0 else "medium"
            conf = min(0.98, max(0.65, round(0.60 + raw_metrics["underexpose_ratio"], 2)))
            issues.append({
                "type": "underexposure", "severity": sev, "confidence": conf,
                "description": f"Underexposed (Mean brightness: {raw_metrics['mean_brightness']})"
            })

        if raw_metrics["overexpose_ratio"] > 0.25 or raw_metrics["mean_brightness"] > 210.0:
            sev = "high" if raw_metrics["mean_brightness"] > 235.0 else "medium"
            conf = min(0.98, max(0.65, round(0.60 + raw_metrics["overexpose_ratio"], 2)))
            issues.append({
                "type": "overexposure", "severity": sev, "confidence": conf,
                "description": f"Overexposed (Mean brightness: {raw_metrics['mean_brightness']})"
            })

        if raw_metrics["noise_sigma"] > 15.0 or raw_metrics["snr_db"] < 18.0:
            sev = "high" if raw_metrics["noise_sigma"] > 35.0 else ("medium" if raw_metrics["noise_sigma"] > 22.0 else "low")
            conf = max(0.60, min(0.95, round(raw_metrics["noise_sigma"] / 40.0, 2)))
            issues.append({
                "type": "noise", "severity": sev, "confidence": conf,
                "description": f"Image noise detected (Sigma: {raw_metrics['noise_sigma']})"
            })

        if raw_metrics["std_local_std"] > 28.0 or raw_metrics["max_local_std"] > 75.0:
            issues.append({
                "type": "visual_defect", "severity": "medium", "confidence": 0.78,
                "description": "Localized texture anomaly or structural defect detected."
            })

        # 3. RF Model Prediction
        cnn_result = None

        if self.is_loaded:
            X_in = np.array(feat_vector).reshape(1, -1)
            pred_class = self.classifier.predict(X_in)[0]
            probs = self.classifier.predict_proba(X_in)[0]
            pred_score = float(self.regressor.predict(X_in)[0])

            # Use classifier.classes_ (sklearn order) for exact probability indexing
            rf_class_order = list(self.classifier.classes_)
            class_idx = rf_class_order.index(pred_class)
            ml_confidence = float(probs[class_idx])

            rf_prob_dict = dict(zip(rf_class_order, [float(p) for p in probs]))

            # 4. CNN Prediction & Ensemble blending
            if self.cnn.is_loaded and img_bgr is not None:
                cnn_result = self.cnn.predict(img_bgr)
                if cnn_result and "class_probabilities" in cnn_result:
                    cnn_probs = cnn_result["class_probabilities"]
                    all_classes = sorted(set(list(rf_prob_dict.keys()) + list(cnn_probs.keys())))
                    ensemble_probs = {}
                    for cls in all_classes:
                        rf_p = rf_prob_dict.get(cls, 0.0)
                        cnn_p = cnn_probs.get(cls, 0.0)
                        ensemble_probs[cls] = 0.6 * rf_p + 0.4 * cnn_p

                    pred_class = max(ensemble_probs, key=ensemble_probs.get)
                    ml_confidence = round(ensemble_probs[pred_class], 3)

            # 5. Tree-Agreement Uncertainty Estimation
            try:
                scaler = self.classifier.named_steps["scaler"]
                rf_model = self.classifier.named_steps["rf"]
                X_scaled = scaler.transform(X_in)
                # Decode via rf_model.classes_ since estimators return internal encoded indices
                tree_votes = [
                    rf_model.classes_[int(tree.predict(X_scaled)[0])]
                    for tree in rf_model.estimators_
                ]
                agreement_ratio = sum(1 for v in tree_votes if v == pred_class) / len(tree_votes)
                uncertainty = {
                    "tree_agreement": round(agreement_ratio, 3),
                    "level": "low" if agreement_ratio >= 0.85 else ("medium" if agreement_ratio >= 0.6 else "high"),
                    "note": "Fraction of the RF's 120 trees that voted for the predicted class. Not a calibrated probability."
                }
            except Exception as e:
                logger.warning(f"Could not compute RF uncertainty estimate: {e}")

            quality_score = round(max(0.0, min(100.0, pred_score)), 1)
        else:
            base_q = 90.0
            if any(i["severity"] == "high" for i in issues):
                base_q -= 40.0
            if any(i["severity"] == "medium" for i in issues):
                base_q -= 20.0
            if any(i["severity"] == "low" for i in issues):
                base_q -= 10.0
            quality_score = round(max(0.0, min(100.0, base_q)), 1)
            pred_class = "ACCEPTABLE" if quality_score >= 75 else ("DEGRADED" if quality_score >= 45 else "DEFECTIVE")
            ml_confidence = 0.85

        # 6. Final Quality Label Assignment
        if quality_score >= 75.0 and not any(i["severity"] in ("high", "medium") for i in issues):
            quality_label = "ACCEPTABLE"
        elif quality_score < 45.0 or any(i["severity"] == "high" for i in issues):
            quality_label = "DEFECTIVE"
        else:
            quality_label = "DEGRADED"

        # 7. Natural Language Explanation
        if not issues:
            explanation = "Image exhibits excellent sharpness, balanced exposure, minimal noise, and clean structure."
        else:
            issue_types = ", ".join(sorted(set(i["type"] for i in issues)))
            explanation = f"Quality evaluated as {quality_label} (Score: {quality_score}/100) due to: {issue_types}."

        return {
            "quality_score": quality_score,
            "quality_label": quality_label,
            "issues": issues,
            "explanation": explanation,
            "predicted_class": pred_class,
            "ml_confidence": round(ml_confidence, 2),
            "cnn_prediction": cnn_result,
            "uncertainty": uncertainty,
        }
