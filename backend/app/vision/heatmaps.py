"""
Heatmap & Explainability Visualizer Module.
Generates local variance anomaly maps, sharpness defect heatmaps, and noise density maps
alpha-blended over the input image for interactive explainability.
"""

import cv2
import numpy as np
from PIL import Image

def generate_quality_heatmap(img_np: np.ndarray, defect_type: str = "general") -> np.ndarray:
    """
    Generates a high-contrast OpenCV heatmap overlay highlighting regions with potential defects,
    severe blur, extreme noise, or local anomalies.
    
    Returns: BGR numpy array representing the heatmap image.
    """
    if img_np is None or img_np.size == 0:
        raise ValueError("Invalid image for heatmap generation.")

    # Convert to grayscale
    if len(img_np.shape) == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        color_base = img_np.copy()
    else:
        gray = img_np
        color_base = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    h, w = gray.shape

    if defect_type == "blur":
        # Local sharpness map via Laplacian magnitude
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_64F))
        # High values mean sharp, inverted (low values) mean blurry
        heat_map_raw = 255.0 - cv2.normalize(lap, None, 0, 255, cv2.NORM_MINMAX)
        heat_map_raw = cv2.GaussianBlur(heat_map_raw, (21, 21), 0)

    elif defect_type == "noise":
        # High frequency noise map via residual
        med = cv2.medianBlur(gray, 5)
        residual = cv2.absdiff(gray, med)
        heat_map_raw = cv2.normalize(residual, None, 0, 255, cv2.NORM_MINMAX)
        heat_map_raw = cv2.GaussianBlur(heat_map_raw.astype(np.float32), (15, 15), 0)

    elif defect_type in ("underexposure", "overexposure"):
        # Highlight extreme brightness regions
        if defect_type == "underexposure":
            diff = np.maximum(0.0, 50.0 - gray.astype(np.float32))
        else:
            diff = np.maximum(0.0, gray.astype(np.float32) - 200.0)
        heat_map_raw = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        heat_map_raw = cv2.GaussianBlur(heat_map_raw, (15, 15), 0)

    else:
        # General defect / local variance anomaly map
        # Local standard deviation filter using OpenCV square kernel
        mean = cv2.blur(gray.astype(np.float32), (15, 15))
        sqr_mean = cv2.blur((gray.astype(np.float32))**2, (15, 15))
        local_var = np.maximum(0.0, sqr_mean - mean**2)
        local_std = np.sqrt(local_var)
        
        # High local std anomaly
        anomaly = np.abs(gray.astype(np.float32) - mean) + local_std
        heat_map_raw = cv2.normalize(anomaly, None, 0, 255, cv2.NORM_MINMAX)
        heat_map_raw = cv2.GaussianBlur(heat_map_raw, (15, 15), 0)

    # Convert normalized float map to uint8
    heat_map_uint8 = np.clip(heat_map_raw, 0, 255).astype(np.uint8)

    # Apply Jet colormap
    color_map = cv2.applyColorMap(heat_map_uint8, cv2.COLORMAP_JET)

    # Blend original base image with heatmap (alpha = 0.55 base, 0.45 heatmap)
    blended = cv2.addWeighted(color_base, 0.55, color_map, 0.45, 0)

    return blended
