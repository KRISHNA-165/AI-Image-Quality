"""
Unit tests for Computer Vision Feature Extraction, Corruption Detection,
Heatmaps, and CNN model definition.
"""

import io
import pytest
import numpy as np
import cv2
from PIL import Image

from backend.app.vision.extractor import extract_image_features
from backend.app.vision.corrupt_detector import check_file_integrity, analyze_corruption_features
from backend.app.vision.heatmaps import generate_quality_heatmap


def test_extract_image_features_clean():
    """Test feature extraction on a crisp synthetic image with sharp edges."""
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (200, 200), (255, 255, 255), -1)
    cv2.circle(img, (128, 128), 40, (0, 0, 255), -1)

    result = extract_image_features(img)

    assert "feature_vector" in result
    assert len(result["feature_vector"]) == 14
    assert result["raw_metrics"]["laplacian_variance"] > 100.0
    assert result["raw_metrics"]["mean_brightness"] > 20.0


def test_fft_ratio_varies_with_blur():
    """
    Regression test: FFT high-frequency ratio must actually decrease when
    image is blurred. (Fixed bug: cv2.circle was drawing on throwaway copy.)
    """
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    cv2.rectangle(img, (30, 30), (220, 220), (200, 200, 200), -1)
    cv2.circle(img, (128, 128), 50, (0, 0, 255), -1)

    feat_sharp = extract_image_features(img)
    blurred = cv2.GaussianBlur(img, (21, 21), 0)
    feat_blurry = extract_image_features(blurred)

    # FFT ratio should be meaningfully lower for blurred image
    sharp_ratio = feat_sharp["raw_metrics"]["fft_high_freq_ratio"]
    blurry_ratio = feat_blurry["raw_metrics"]["fft_high_freq_ratio"]

    # Both should be non-constant and the sharp image should have higher ratio
    assert sharp_ratio != 1.0, "FFT ratio should not be constant 1.0 (bug check)"
    assert sharp_ratio > blurry_ratio, (
        f"Sharp FFT ratio ({sharp_ratio}) should be > blurry ({blurry_ratio})"
    )


def test_corrupt_detector():
    """Test file integrity validation with valid and invalid byte streams."""
    img = Image.new("RGB", (64, 64), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_png_bytes = buf.getvalue()

    is_valid, err_msg, meta = check_file_integrity(valid_png_bytes)
    assert is_valid is True
    assert err_msg is None
    assert meta.get("format") == "png"

    invalid_bytes = b"CORRUPT_HEADER_STREAM_TEST"
    is_valid_inv, err_msg_inv, meta_inv = check_file_integrity(invalid_bytes)
    assert is_valid_inv is False
    assert err_msg_inv is not None


def test_heatmap_generation():
    """Test heatmap overlay generation for different defect types."""
    img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    for defect_type in ["blur", "noise", "underexposure", "overexposure", "general"]:
        heatmap = generate_quality_heatmap(img, defect_type=defect_type)
        assert heatmap is not None
        assert heatmap.shape == (100, 100, 3)


def test_cnn_model_forward_pass():
    """Test that the DefectCNN model runs a forward pass without errors."""
    try:
        import torch
        from backend.app.ml.cnn_model import DefectCNN
    except ImportError:
        pytest.skip("PyTorch not installed")

    model = DefectCNN(num_classes=6)
    model.eval()

    # Synthetic 64x64 RGB input
    x = torch.randn(2, 3, 64, 64)
    with torch.no_grad():
        out = model(x)

    assert out.shape == (2, 6), f"Expected (2, 6), got {out.shape}"
    assert model.parameter_count() > 0


def test_cnn_model_classes():
    """Verify CNN CLASSES list is sorted alphabetically (required for consistent label mapping)."""
    try:
        from backend.app.ml.cnn_model import DefectCNN
    except ImportError:
        pytest.skip("PyTorch not installed")

    assert DefectCNN.CLASSES == sorted(DefectCNN.CLASSES), "CLASSES must be in alphabetical order"
    assert len(DefectCNN.CLASSES) == 6
