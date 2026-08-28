"""
Synthetic Dataset Generator and AI Model Training Pipeline.

Changes from v1:
 - Degradation ranges widened to include mild/borderline cases that overlap
   between classes, eliminating the trivial 100% accuracy problem.
 - FFT feature is now non-constant (extractor bug fixed), giving the RF
   a genuine 14th feature to learn from.
 - Generates both per-class image arrays (for CNN) and feature vectors (for RF).
"""

import os
import sys
import json
import random
from datetime import datetime, timezone
import numpy as np
import cv2
from PIL import Image, ImageDraw
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
import joblib

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from backend.app.vision.extractor import extract_image_features

MODEL_VERSION = "1.1.0"
CLASSES = ["ACCEPTABLE", "BLUR", "UNDEREXPOSURE", "OVEREXPOSURE", "NOISE", "DEFECTIVE"]


def generate_base_synthetic_image(width=256, height=256) -> np.ndarray:
    """Generates a clean synthetic base image with geometric shapes and gradients."""
    img = Image.new("RGB", (width, height), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)

    for _ in range(random.randint(3, 7)):
        x1, y1 = random.randint(0, width // 2), random.randint(0, height // 2)
        x2, y2 = random.randint(width // 2, width), random.randint(height // 2, height)
        color = (random.randint(50, 220), random.randint(50, 220), random.randint(50, 220))
        draw.rectangle([x1, y1, x2, y2], fill=color, outline=(20, 20, 20), width=2)

    for _ in range(random.randint(2, 5)):
        cx, cy = random.randint(30, width - 30), random.randint(30, height - 30)
        r = random.randint(15, 45)
        color = (random.randint(80, 240), random.randint(80, 240), random.randint(80, 240))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(10, 10, 10), width=2)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def apply_degradation(img_bgr: np.ndarray, category: str) -> tuple:
    """
    Applies synthetic degradation according to category.
    HARDENED: ranges now include mild/borderline cases that create genuine
    overlap between classes, so the classifier can't trivially separate them.
    Returns: (degraded_img_bgr, target_quality_score)
    """
    img = img_bgr.copy()
    h, w = img.shape[:2]

    if category == "ACCEPTABLE":
        # Some ACCEPTABLE images get very light degradations to create overlap
        r = random.random()
        if r < 0.3:
            # Light Gaussian blur (k=3 or 5) — borderline with BLUR class
            ksize = random.choice([3, 5])
            img = cv2.GaussianBlur(img, (ksize, ksize), 0)
        elif r < 0.5:
            # Light noise or slight brightness shift
            if random.random() < 0.5:
                noise = np.random.normal(0, random.uniform(3, 8), img.shape)
                img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            else:
                shift = random.uniform(0.85, 1.15)
                img = np.clip(img.astype(np.float32) * shift, 0, 255).astype(np.uint8)
        score = float(random.randint(78, 98))
        return img, score

    elif category == "BLUR":
        # Range from mild (k=5) to heavy (k=27) — mild overlaps ACCEPTABLE
        ksize = random.choice([5, 7, 9, 11, 15, 21, 27])
        sigma = random.uniform(0, ksize / 2.0)
        img = cv2.GaussianBlur(img, (ksize, ksize), sigma)
        # Mild blur gets higher score
        score = float(max(15, min(65, 70 - ksize * 2 + random.randint(-5, 5))))
        return img, score

    elif category == "UNDEREXPOSURE":
        # From mild darkening (0.55) to extreme (0.08)
        factor = random.uniform(0.08, 0.55)
        img = np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        score = float(max(10, min(55, int(factor * 100) + random.randint(0, 5))))
        return img, score

    elif category == "OVEREXPOSURE":
        # From mild (1.4x) to extreme (3.5x) — mild overlaps ACCEPTABLE
        factor = random.uniform(1.4, 3.5)
        img = np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        score = float(max(10, min(55, int(100 - factor * 18) + random.randint(-5, 5))))
        return img, score

    elif category == "NOISE":
        # From light (sigma=10) to heavy (sigma=65)
        sigma_noise = random.uniform(10, 65)
        noise = np.random.normal(0, sigma_noise, img.shape)
        img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        score = float(max(15, min(60, int(70 - sigma_noise))))
        return img, score

    elif category == "DEFECTIVE":
        # Scratches, dead blocks, color corruption — variable severity
        n_scratches = random.randint(1, 7)
        for _ in range(n_scratches):
            x1, y1 = random.randint(0, w), random.randint(0, h)
            x2, y2 = random.randint(0, w), random.randint(0, h)
            color = random.choice([(0, 0, 0), (255, 255, 255), (255, 0, 255)])
            cv2.line(img, (x1, y1), (x2, y2), color, thickness=random.randint(2, 8))

        # Sometimes add dead rectangle block
        if random.random() < 0.5:
            bw, bh = random.randint(20, 60), random.randint(20, 60)
            bx, by = random.randint(0, max(1, w - bw)), random.randint(0, max(1, h - bh))
            cv2.rectangle(img, (bx, by), (bx + bw, by + bh), (255, 0, 255), -1)

        score = float(random.randint(10, 45))
        return img, score

    return img, 70.0


def run_training_pipeline():
    """Builds hardened synthetic dataset, trains RF models, evaluates, and serializes."""
    random.seed(42)
    np.random.seed(42)
    print("=" * 60)
    print("RF MODEL TRAINING PIPELINE (Hardened Synthetic Data)")
    print("=" * 60)

    samples_per_class = 200
    X_features = []
    y_class = []
    y_scores = []

    for cls in CLASSES:
        print(f"  -> Generating class: {cls} ({samples_per_class} samples)")
        for _ in range(samples_per_class):
            base_img = generate_base_synthetic_image()
            deg_img, quality_score = apply_degradation(base_img, cls)
            try:
                feat_dict = extract_image_features(deg_img)
                X_features.append(feat_dict["feature_vector"])
                y_class.append(cls)
                y_scores.append(quality_score)
            except Exception as e:
                print(f"     Error extracting features: {e}")

    X = np.array(X_features)
    y_cls = np.array(y_class)
    y_reg = np.array(y_scores)
    print(f"\nDataset: {len(X)} samples, {len(X[0])} features each")

    # Split train/test (80/20)
    X_train, X_test, y_train_c, y_test_c, y_train_r, y_test_r = train_test_split(
        X, y_cls, y_reg, test_size=0.20, random_state=42, stratify=y_cls
    )

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    print("\nTraining Random Forest Classifier (120 trees, max_depth=15)...")
    classifier_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(n_estimators=120, max_depth=15, random_state=42))
    ])
    classifier_pipeline.fit(X_train, y_train_c)

    print("Training Random Forest Regressor (100 trees)...")
    regressor_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf_reg", RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42))
    ])
    regressor_pipeline.fit(X_train, y_train_r)

    # Evaluation
    y_pred_c = classifier_pipeline.predict(X_test)
    acc = float(accuracy_score(y_test_c, y_pred_c))
    f1_macro = float(f1_score(y_test_c, y_pred_c, average="macro"))

    print("\n" + "=" * 50)
    print("EVALUATION RESULTS (Unseen Test Set)")
    print("=" * 50)
    print(f"Test Accuracy:   {acc * 100:.2f}%")
    print(f"Macro F1-Score:  {f1_macro:.4f}")
    print("\nClassification Report:")
    report_str = classification_report(y_test_c, y_pred_c, target_names=CLASSES)
    print(report_str)

    conf_mat = confusion_matrix(y_test_c, y_pred_c, labels=CLASSES).tolist()

    # Feature importances
    feature_names = [
        "laplacian_var", "tenengrad", "fft_high_freq_ratio", "mean_brightness",
        "median_brightness", "underexpose_ratio", "overexpose_ratio", "rms_contrast",
        "noise_sigma", "residual_noise_std", "snr_db", "mean_saturation",
        "max_local_std", "std_local_std"
    ]
    rf_model = classifier_pipeline.named_steps["rf"]
    importances = rf_model.feature_importances_.tolist()
    feature_imp_dict = dict(zip(feature_names, [round(float(imp), 4) for imp in importances]))

    # Save
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models_store"))
    os.makedirs(models_dir, exist_ok=True)

    metrics_payload = {
        "model_version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "classes": CLASSES,
        "confusion_matrix": conf_mat,
        "feature_importances": feature_imp_dict,
        "sample_count": len(X),
        "test_sample_count": len(X_test)
    }

    with open(os.path.join(models_dir, "metrics.json"), "w") as f:
        json.dump(metrics_payload, f, indent=2)

    model_bundle = {
        "classifier": classifier_pipeline,
        "regressor": regressor_pipeline,
        "classes": CLASSES,
        "feature_names": feature_names
    }
    joblib.dump(model_bundle, os.path.join(models_dir, "model.joblib"))
    print(f"\nRF model saved to {os.path.join(models_dir, 'model.joblib')}")

    # Generate sample test images
    sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample_images"))
    os.makedirs(sample_dir, exist_ok=True)

    print("\nGenerating sample test images...")
    for cls in CLASSES:
        base = generate_base_synthetic_image(384, 384)
        sample, _ = apply_degradation(base, cls)
        cv2.imwrite(os.path.join(sample_dir, f"sample_{cls.lower()}.png"), sample)

    # Corrupted test image
    with open(os.path.join(sample_dir, "sample_corrupt.png"), "wb") as f:
        f.write(b"CORRUPT_HEADER_INVALID_BYTE_STREAM_TEST_CONTENT")

    print("Sample images created. RF pipeline complete.\n")


if __name__ == "__main__":
    run_training_pipeline()
