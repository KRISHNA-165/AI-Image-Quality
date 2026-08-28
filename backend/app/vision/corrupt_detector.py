"""
Image Corruption and Integrity Detection Module.
Detects truncated files, unreadable byte headers, uniform/dead channels,
extreme color cast, and zero-variance regions.
"""

import io
from typing import Optional, Tuple, Dict, Any
import cv2
import numpy as np
from PIL import Image, ImageFile

# Ensure PIL raises exception on truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = False

MAGIC_NUMBERS = {
    "jpeg": [b"\xFF\xD8\xFF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],
    "bmp": [b"BM"],
}

def check_file_integrity(file_bytes: bytes) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validates byte-level header and structure of uploaded file.
    Returns: (is_valid, error_message, metadata)
    """
    if not file_bytes or len(file_bytes) < 10:
        return False, "File is empty or too small", {"byte_size": len(file_bytes)}

    # Check magic numbers
    format_detected = None
    for fmt, headers in MAGIC_NUMBERS.items():
        if any(file_bytes.startswith(h) for h in headers):
            format_detected = fmt
            break

    if not format_detected:
        return False, "Unsupported file format or corrupt header", {"byte_size": len(file_bytes)}

    # Test PIL loading and verify completeness
    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img.verify()  # Verifies file header and block integrity
        
        # Re-open for image properties inspection
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img.load()  # Decodes entire pixel buffer
        width, height = pil_img.size
        
        if width <= 0 or height <= 0:
            return False, "Invalid image dimensions", {"width": width, "height": height}

    except Exception as e:
        return False, f"Image decoding error: {str(e)}", {"byte_size": len(file_bytes)}

    return True, None, {"format": format_detected, "width": width, "height": height, "byte_size": len(file_bytes)}


def analyze_corruption_features(img_np: np.ndarray) -> Dict[str, Any]:
    """
    Analyzes numpy BGR/Grayscale image array for visual corruption metrics:
    - Dead channels (all 0 or all 255)
    - Extreme color cast (imbalance between color channels)
    - Zero/near-zero total variance
    - Missing channel ratio
    """
    if img_np is None or img_np.size == 0:
        return {
            "is_corrupt": True,
            "corruption_reason": "Empty image array",
            "dead_channel_count": 3,
            "color_cast_score": 1.0,
            "variance": 0.0
        }

    is_color = len(img_np.shape) == 3 and img_np.shape[2] == 3
    dead_channels = 0
    channel_means = []
    channel_stds = []

    if is_color:
        for c in range(3):
            ch = img_np[:, :, c]
            std = float(np.std(ch))
            mean = float(np.mean(ch))
            channel_stds.append(std)
            channel_means.append(mean)
            if std < 0.1 or mean in (0.0, 255.0):
                dead_channels += 1

        # Color cast score: deviation between channel means relative to global mean
        overall_mean = np.mean(channel_means) + 1e-6
        color_cast_score = float(np.std(channel_means) / overall_mean)
    else:
        std = float(np.std(img_np))
        mean = float(np.mean(img_np))
        channel_stds = [std]
        channel_means = [mean]
        if std < 0.1:
            dead_channels = 1
        color_cast_score = 0.0

    total_var = float(np.var(img_np))
    is_corrupt = (dead_channels > 0 and (is_color and dead_channels >= 2)) or (total_var < 0.5)

    return {
        "is_corrupt": is_corrupt,
        "corruption_reason": "Dead channels or uniform image" if is_corrupt else None,
        "dead_channel_count": dead_channels,
        "color_cast_score": round(color_cast_score, 4),
        "total_variance": round(total_var, 4),
        "channel_stds": [round(s, 2) for s in channel_stds],
        "channel_means": [round(m, 2) for m in channel_means],
    }
