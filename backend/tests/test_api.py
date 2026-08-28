"""
Pytest integration tests for FastAPI REST API Endpoints.
"""

import os
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "ok"]
    assert "database" in data
    assert "model_loaded" in data

def test_root_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "cnn_model_loaded" in data

def test_model_info():
    response = client.get("/api/v1/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "feature_importances" in data

def test_analyze_valid_image():
    # Generate a simple in-memory PNG image
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    files = {"file": ("test_sample.png", img_bytes, "image/png")}
    response = client.post("/api/v1/analyze", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert "quality_score" in data
    assert "quality_label" in data
    assert data["quality_label"] in ["ACCEPTABLE", "DEGRADED", "DEFECTIVE"]
    assert "issues" in data
    assert "metrics" in data
    assert data["image_url"].startswith("/storage/uploads/")

def test_analyze_invalid_file():
    files = {"file": ("bad_file.txt", b"INVALID_BYTE_STREAM_HEADER", "text/plain")}
    response = client.post("/api/v1/analyze", files=files)
    
    assert response.status_code == 201  # Handles corrupt gracefully and marks DEFECTIVE
    data = response.json()
    assert data["quality_label"] == "DEFECTIVE"
    assert data["quality_score"] == 0.0

def test_get_analyses_history():
    response = client.get("/api/v1/analyses?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "data" in data
    assert isinstance(data["data"], list)

def test_analyze_reports_rf_uncertainty():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_images", "sample_acceptable.png")
    if not os.path.exists(sample_path):
        pytest.skip("sample_acceptable.png not generated yet -- run train.py first")

    with open(sample_path, "rb") as f:
        files = {"file": ("sample_acceptable.png", f.read(), "image/png")}
    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 201
    data = response.json()

    uncertainty = data["metrics"].get("uncertainty")
    assert uncertainty is not None, "uncertainty block missing from metrics"
    assert 0.0 <= uncertainty["tree_agreement"] <= 1.0
    assert uncertainty["level"] in ("low", "medium", "high")

    ml_confidence = data["metrics"]["ml_ensemble"]["confidence"]
    assert abs(uncertainty["tree_agreement"] - ml_confidence) < 0.5

def test_metrics_endpoint():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "http" in data
    assert "total_requests" in data["http"]
    assert "latency_ms" in data["http"]
    assert "domain_metrics" in data
    assert "system" in data
    assert "uptime_seconds" in data
