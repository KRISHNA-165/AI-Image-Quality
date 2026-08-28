"""
Computer Vision Feature Extractor.
Derives quantitative metrics for sharpness, exposure, noise, contrast, color, and local anomalies.
"""

import cv2
import numpy as np

def extract_image_features(img_np: np.ndarray) -> dict:
    """
    Extracts a 14-dimensional feature vector and structured diagnostic metrics
    from a BGR or Grayscale numpy image array.
    """
    if img_np is None or img_np.size == 0:
        raise ValueError("Invalid or empty image array provided to feature extractor.")

    # Convert BGR to Grayscale if needed
    if len(img_np.shape) == 3 and img_np.shape[2] == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img_np, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        mean_saturation = float(np.mean(sat))
    else:
        gray = img_np
        mean_saturation = 0.0

    height, width = gray.shape
    total_pixels = float(height * width)

    # -------------------------------------------------------------
    # 1. Blur & Sharpness Features
    # -------------------------------------------------------------
    # Laplacian Variance
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # Tenengrad Gradient Magnitude
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = float(np.mean(gx**2 + gy**2))

    # FFT High Frequency Ratio
    f = np.fft.fft2(gray.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = 20.0 * np.log(np.abs(fshift) + 1e-6)
    
    # Mask center (low frequencies)
    cy, cx = height // 2, width // 2
    r = min(height, width) // 10
    mask_u8 = np.ones((height, width), dtype=np.uint8)
    cv2.circle(mask_u8, (cx, cy), max(r, 5), 0, -1)
    mask = mask_u8.astype(bool)
    
    high_freq_power = float(np.mean(magnitude_spectrum[mask]))
    total_freq_power = float(np.mean(magnitude_spectrum)) + 1e-6
    fft_high_freq_ratio = round(high_freq_power / total_freq_power, 4)

    # -------------------------------------------------------------
    # 2. Exposure & Brightness Features
    # -------------------------------------------------------------
    mean_brightness = float(np.mean(gray))
    median_brightness = float(np.median(gray))
    p5 = float(np.percentile(gray, 5))
    p95 = float(np.percentile(gray, 95))

    underexposed_pixels = float(np.sum(gray < 30))
    overexposed_pixels = float(np.sum(gray > 225))

    underexpose_ratio = round(underexposed_pixels / total_pixels, 4)
    overexpose_ratio = round(overexposed_pixels / total_pixels, 4)

    # RMS Contrast
    rms_contrast = float(np.std(gray))

    # -------------------------------------------------------------
    # 3. Image Noise Features
    # -------------------------------------------------------------
    # Immerkær noise estimation via fast convolution
    # H kernel = [[1, -2, 1], [-2, 4, -2], [1, -2, 1]]
    kernel = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    sigma_n = float(np.sum(np.abs(cv2.filter2D(gray.astype(np.float64), -1, kernel))))
    sigma_n = sigma_n * np.sqrt(0.5 * np.pi) / (6.0 * (width - 2) * (height - 2) + 1e-6)

    # Median Residual Noise
    median_blur = cv2.medianBlur(gray, 3)
    noise_residual = np.abs(gray.astype(np.float64) - median_blur.astype(np.float64))
    residual_noise_std = float(np.std(noise_residual))

    # Signal to Noise Ratio (SNR in dB)
    signal_power = float(np.mean(gray**2))
    noise_power = (sigma_n ** 2) + 1e-6
    snr_db = round(float(10 * np.log10(signal_power / noise_power)), 2) if noise_power > 0 else 50.0

    # -------------------------------------------------------------
    # 4. Local Anomaly & Texture Defect Features
    # -------------------------------------------------------------
    # Local variance map over 16x16 blocks
    blk_size = 16
    h_blks, w_blks = height // blk_size, width // blk_size
    if h_blks > 0 and w_blks > 0:
        cropped_gray = gray[:h_blks * blk_size, :w_blks * blk_size]
        blocks = cropped_gray.reshape(h_blks, blk_size, w_blks, blk_size).swapaxes(1, 2)
        block_stds = np.std(blocks, axis=(2, 3))
        max_local_std = float(np.max(block_stds))
        min_local_std = float(np.min(block_stds))
        std_local_std = float(np.std(block_stds))
    else:
        max_local_std = rms_contrast
        min_local_std = rms_contrast
        std_local_std = 0.0

    # Build numeric vector for ML model
    feature_vector = [
        round(lap_var, 4),
        round(tenengrad, 4),
        round(fft_high_freq_ratio, 4),
        round(mean_brightness, 4),
        round(median_brightness, 4),
        round(underexpose_ratio, 4),
        round(overexpose_ratio, 4),
        round(rms_contrast, 4),
        round(sigma_n, 4),
        round(residual_noise_std, 4),
        round(snr_db, 4),
        round(mean_saturation, 4),
        round(max_local_std, 4),
        round(std_local_std, 4)
    ]

    # Map scores to intuitive 0-100 normalized scales
    sharpness_score = min(100.0, max(0.0, (lap_var / 350.0) * 100.0))
    brightness_score = min(100.0, max(0.0, 100.0 - abs(mean_brightness - 128.0) * 0.75))
    contrast_score = min(100.0, max(0.0, (rms_contrast / 64.0) * 100.0))
    noise_score = min(100.0, max(0.0, (sigma_n / 25.0) * 100.0))

    return {
        "feature_vector": feature_vector,
        "raw_metrics": {
            "laplacian_variance": round(lap_var, 2),
            "tenengrad": round(tenengrad, 2),
            "fft_high_freq_ratio": fft_high_freq_ratio,
            "mean_brightness": round(mean_brightness, 2),
            "median_brightness": round(median_brightness, 2),
            "p5_dark": round(p5, 2),
            "p95_bright": round(p95, 2),
            "underexpose_ratio": underexpose_ratio,
            "overexpose_ratio": overexpose_ratio,
            "rms_contrast": round(rms_contrast, 2),
            "noise_sigma": round(sigma_n, 2),
            "residual_noise_std": round(residual_noise_std, 2),
            "snr_db": snr_db,
            "mean_saturation": round(mean_saturation, 2),
            "max_local_std": round(max_local_std, 2),
            "std_local_std": round(std_local_std, 2)
        },
        "normalized_scores": {
            "sharpness_score": round(sharpness_score, 1),
            "brightness_score": round(brightness_score, 1),
            "contrast_score": round(contrast_score, 1),
            "noise_score": round(noise_score, 1)
        }
    }
