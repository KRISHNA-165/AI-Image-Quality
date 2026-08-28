"""
DefectCNN — Lightweight Convolutional Neural Network for Image Quality Classification.

A 4-layer CNN that processes 64x64 RGB image thumbnails and outputs class
probabilities over the 6 quality/defect categories. Intentionally kept small
(~155K parameters) so it trains in minutes on CPU.

Architecture:
  Input: 3x64x64 RGB thumbnail
  -> Conv2d(3, 16, 3) + BatchNorm + ReLU + MaxPool(2)
  -> Conv2d(16, 32, 3) + BatchNorm + ReLU + MaxPool(2)
  -> Conv2d(32, 64, 3) + BatchNorm + ReLU + AdaptiveAvgPool(4)
  -> Flatten -> Linear(1024, 128) + ReLU + Dropout(0.3)
  -> Linear(128, 6) -> softmax
"""

import os
import json
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import cv2
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = object


class DefectCNN(nn.Module if TORCH_AVAILABLE else object):
    """Lightweight CNN for image quality defect classification."""

    CLASSES = ["ACCEPTABLE", "BLUR", "DEFECTIVE", "NOISE", "OVEREXPOSURE", "UNDEREXPOSURE"]
    INPUT_SIZE = 64  # Expected input: 3 x 64 x 64

    def __init__(self, num_classes: int = 6):
        if not TORCH_AVAILABLE:
            return
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=0),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=0),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=0),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(4),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

    def parameter_count(self) -> int:
        """Returns total number of trainable parameters."""
        if not TORCH_AVAILABLE:
            return 0
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class CNNQualityClassifier:
    """Fail-soft wrapper for DefectCNN inference and metric management."""

    def __init__(self, weights_path: str = None):
        if weights_path is None:
            weights_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../models_store/cnn_model.pt")
            )

        self.weights_path = weights_path
        self.model = None
        self.is_loaded = False
        self.metrics_info = {}
        self.classes = DefectCNN.CLASSES

        self.load_model()

    def load_model(self):
        """Loads serialized PyTorch weights and evaluation metrics."""
        if not TORCH_AVAILABLE:
            self.is_loaded = False
            return

        if os.path.exists(self.weights_path):
            try:
                self.model = DefectCNN(num_classes=len(self.classes))
                self.model.load_state_dict(torch.load(self.weights_path, map_location="cpu"))
                self.model.eval()
                self.is_loaded = True

                metrics_file = os.path.join(os.path.dirname(self.weights_path), "cnn_metrics.json")
                if os.path.exists(metrics_file):
                    with open(metrics_file, "r") as f:
                        self.metrics_info = json.load(f)

                logger.info(f"CNNQualityClassifier: model loaded from {self.weights_path}")
            except Exception as e:
                logger.error(f"CNNQualityClassifier: failed to load model weights: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def predict(self, img_bgr: np.ndarray) -> dict:
        """
        Runs CNN inference on a BGR image array.
        Returns:
            {
                "predicted_class": "BLUR",
                "class_probabilities": {...},
                "confidence": 0.94
            }
            or None if model is unavailable.
        """
        if not self.is_loaded or img_bgr is None or not TORCH_AVAILABLE:
            return None

        try:
            thumb = cv2.resize(img_bgr, (DefectCNN.INPUT_SIZE, DefectCNN.INPUT_SIZE), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            tensor = torch.from_numpy(
                np.transpose(rgb, (2, 0, 1)).astype(np.float32) / 255.0
            ).unsqueeze(0)

            with torch.no_grad():
                logits = self.model(tensor)
                probs = torch.softmax(logits, dim=1).squeeze().numpy()

            prob_dict = {cls: round(float(probs[i]), 4) for i, cls in enumerate(self.classes)}
            predicted_class = max(prob_dict, key=prob_dict.get)
            confidence = float(prob_dict[predicted_class])

            return {
                "predicted_class": predicted_class,
                "class_probabilities": prob_dict,
                "confidence": round(confidence, 3)
            }
        except Exception as e:
            logger.error(f"CNNQualityClassifier: prediction error: {e}")
            return None
