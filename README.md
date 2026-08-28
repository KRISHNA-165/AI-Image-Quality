# QualiVision AI — Image Quality & Defect Detection Engine

> **Technical Assessment Submission**: Full-Stack AI Application for Automatic Image Quality Assessment, Defect Classification, Explainability Heatmaps, and Persistence.
> **Zero External API Dependencies**: 100% self-contained computer vision engine, local PyTorch CNN, and Scikit-Learn Random Forest ensemble.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture & Model Inference Process](#2-system-architecture--model-inference-process)
3. [Prerequisites & System Requirements](#3-prerequisites--system-requirements)
4. [Computer Vision Engine & Feature Reasoning](#4-computer-vision-engine--feature-reasoning)
5. [AI / Machine Learning & Model Training](#5-ai--machine-learning--model-training)
6. [Database Setup](#6-database-setup)
7. [Backend REST API Specification & Examples](#7-backend-rest-api-specification--examples)
8. [Frontend Application & Heatmap Inspector](#8-frontend-application--heatmap-inspector)
9. [Performance, Concurrency & Monitoring](#9-performance-concurrency--monitoring)
10. [Evaluation Results & Experimental Rigor](#10-evaluation-results--experimental-rigor)
11. [Installation & Deployment Instructions](#11-installation--deployment-instructions)
12. [Docker & Docker Compose Instructions](#12-docker--docker-compose-instructions)
13. [Sample Test Images](#13-sample-test-images)
14. [Automated Testing & CI/CD](#14-automated-testing--cicd)
15. [Troubleshooting Guide](#15-troubleshooting-guide)

---

## 1. Project Overview

QualiVision AI evaluates uploaded images to automatically identify common visual defects (Blur, Underexposure, Overexposure, Image Noise, Byte Corruption, and Texture Anomaly Defects). It produces a 0-100 continuous Quality Score, a 3-tier Quality Label (`ACCEPTABLE`, `DEGRADED`, `DEFECTIVE`), OpenCV Jet explainability heatmaps, tree-agreement uncertainty estimates, and structured natural language summaries.

---

## 2. System Architecture & Model Inference Process

### System Architecture
```
                             ┌──────────────────────────────────────────────┐
                             │              React SPA Frontend              │
                             │      (Vite + Glassmorphism UI + Heatmap)     │
                             └──────────────────────┬───────────────────────┘
                                                    │ HTTP / REST API
                                                    ▼
                             ┌──────────────────────────────────────────────┐
                             │               FastAPI Backend                │
                             │        (Validation, Routing, Storage)        │
                             └──────────┬────────────────────────┬──────────┘
                                        │                        │
                                        ▼                        ▼
       ┌──────────────────────────────────────────┐    ┌──────────────────────────────────┐
       │          Computer Vision Engine          │    │     Hybrid Machine Learning      │
       │  • Blur (Laplacian, Tenengrad, FFT)      │    │             Ensemble             │
       │  • Exposure (Histogram, Clipping)        │    │ • Random Forest Classifier       │
       │  • Noise (Immerkær, Median Residual)     │    │ • DefectCNN PyTorch Deep Learning│
       │  • Corruption (Magic Header Check)       │    │ • Quality Score Regressor        │
       │  • Local Texture Variance Anomaly Map    │    │ • Tree Agreement Uncertainty     │
       └──────────────────────────────────────────┘    └──────────────────────────────────┘
                                        │                        │
                                        └────────────────┬───────┘
                                                         ▼
                                     ┌──────────────────────────────────────┐
                                     │     SQLite Database Persistence      │
                                     │    (Analysis History & Metadata)     │
                                     └──────────────────────────────────────┘
```

### Model Inference Process Pipeline
When an image is submitted (`POST /api/v1/analyze`):

1. **Byte Integrity Check**: Validates magic file headers (`JPEG`, `PNG`, `WEBP`, `BMP`). If corrupt, returns immediate `DEFECTIVE` result.
2. **OpenCV Pixel Decoding**: Decodes binary byte stream into a BGR NumPy matrix.
3. **Computer Vision Feature Extraction**: Extracts a 14-dimensional feature vector quantifying Laplacian variance, Tenengrad magnitude, FFT spectral power ratio, mean/median brightness, under/overexposure pixel ratios, RMS contrast, Immerkær noise $\sigma$, SNR in dB, mean saturation, and local block variance anomalies.
4. **Hybrid ML Ensemble Inference**:
   - **Random Forest**: Standard-scaled 14D vector evaluated across 120 decision trees to produce class probabilities and regressed 0-100 quality score.
   - **DefectCNN**: Resized 64×64 RGB thumbnail evaluated through a 4-layer PyTorch ConvNet.
   - **Ensemble Fusion**: Blends class probability distributions (60% RF + 40% CNN) to select final predicted class and confidence.
   - **Uncertainty Estimation**: Calculates individual tree decision agreement ratio across all 120 RF estimators.
5. **Explainability Heatmap Overlay**: Generates an OpenCV Jet colormap defect overlay matching the primary detected issue.
6. **SQLite Database Persistence**: Stores record with metadata, quality metrics, issue breakdown, image URLs, and timestamp.

---

## 3. Prerequisites & System Requirements

- **Python**: `3.10` or higher
- **Node.js**: `18.0` or higher (`npm 9+`)
- **Docker**: `Docker 20.10+` and `Docker Compose v2+` (for containerized deployment)
- **OS**: macOS, Linux (Ubuntu 20.04+), or Windows (WSL2)

---

## 4. Computer Vision Engine & Feature Reasoning

The feature extractor (`backend/app/vision/extractor.py`) derives quantitative metrics:

1. **Blur / Insufficient Sharpness**:
   - **Laplacian Variance** ($\sigma^2(\nabla^2 I)$): Second derivative edge sharpness (< 80.0 indicates blur).
   - **Tenengrad Magnitude** ($\sum |G_x|^2 + |G_y|^2$): Sobel gradient power.
   - **FFT High-Frequency Ratio**: 2D Fourier Transform high-frequency power spectral ratio.
2. **Underexposure & Overexposure**:
   - **Mean/Median Luminance**: Brightness distribution ($I \in [0, 255]$).
   - **Underexposure Ratio**: Proportion of pixels with $I < 30$.
   - **Overexposure Ratio**: Proportion of pixels with $I > 225$.
   - **RMS Contrast**: Standard deviation of pixel intensities ($\sigma_I$).
3. **Image Noise**:
   - **Immerkær Fast Noise Estimator**: Convolves noise kernel $H = \begin{bmatrix} 1 & -2 & 1 \\ -2 & 4 & -2 \\ 1 & -2 & 1 \end{bmatrix}$ to estimate additive Gaussian noise $\sigma_n$.
   - **Median Residual Variance**: Pixel variance relative to 3x3 median blur.
   - **SNR (dB)**: Signal-to-Noise Ratio $10 \log_{10}(P_{\text{signal}} / P_{\text{noise}})$.
4. **Local Anomaly Map**:
   - **Local Standard Deviation Filter**: $16 \times 16$ sliding block variance map highlighting localized scratches and dead pixel clusters.

---

## 5. AI / Machine Learning & Model Training

### Training Pipeline (`train.py` and `train_cnn.py`)
Both models train on a balanced synthetic dataset with continuous, overlapping degradations (mild blurs, subtle exposure shifts, variable noise grain, scratches):

```bash
# 1. Train Random Forest Classifier & Score Regressor (1,200 samples)
PYTHONPATH=. python backend/app/ml/train.py

# 2. Train PyTorch DefectCNN Deep Learning Model (1,500 64x64 thumbnails)
PYTHONPATH=. python backend/app/ml/train_cnn.py
```

### Serialized Model Assets (`backend/models_store/`)
- `model.joblib`: Trained Random Forest classifier & regressor pipelines.
- `cnn_model.pt`: Serialized PyTorch DefectCNN state dict weights (~155K parameters).
- `metrics.json`: JSON payload storing `model_version` ("1.1.0"), `trained_at`, test accuracy, F1 score, and feature importances.
- `cnn_metrics.json`: JSON payload storing CNN accuracy, F1 score, and confusion matrix.

The backend automatically loads these model weights on application startup inside `QualityEvaluator` (`backend/app/ml/evaluator.py`).

---

## 6. Database Setup

QualiVision AI uses **SQLite** for zero-configuration, self-contained persistence.

- **Database File**: `backend/quality_detector.db`
- **Automatic Initialization**: SQLAlchemy automatically creates all required tables and indexes on application launch (`Base.metadata.create_all(bind=engine)`).
- **SQL DDL Reference**: Available in [`database/database_setup.sql`](file:///Users/balakrishnagunda/Desktop/iiith/database/database_setup.sql).

---

## 7. Backend REST API Specification & Examples

Base API URL: `http://localhost:8000/api/v1`

### Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Root health status (`{"status": "ok", "model_loaded": true, "cnn_model_loaded": true}`) |
| `POST` | `/api/v1/analyze` | Single image upload and visual quality assessment |
| `POST` | `/api/v1/analyze/batch` | High-throughput concurrent batch analysis (up to 20 images) |
| `GET` | `/api/v1/analyses` | Paginated analysis history log with search & label filters |
| `GET` | `/api/v1/analyses/{id}` | Detailed analysis record by ID |
| `DELETE` | `/api/v1/analyses/{id}` | Delete record and stored image/heatmap artifacts |
| `GET` | `/api/v1/health` | Service health, memory footprint, uptime, and model load status |
| `GET` | `/api/v1/metrics` | Real-time observability, $p_{50}/p_{95}$ latency distributions, throughput |
| `GET` | `/api/v1/model-info` | Model version, trained timestamp, accuracy, confusion matrix |

### Example Request Commands

#### 1. Single Image Analysis (`POST /api/v1/analyze`)
```bash
curl -X POST -F "file=@backend/sample_images/sample_blur.png" http://localhost:8000/api/v1/analyze
```

#### 2. Root Health Check (`GET /health`)
```bash
curl http://localhost:8000/health
```

#### 3. Real-Time Telemetry & Latency Stats (`GET /api/v1/metrics`)
```bash
curl http://localhost:8000/api/v1/metrics
```

#### 4. Model Information & Confusion Matrix (`GET /api/v1/model-info`)
```bash
curl http://localhost:8000/api/v1/model-info
```

---

## 8. Frontend Application & Heatmap Inspector

Built with React 18, Vite, and Vanilla CSS:
- **Image Analyzer Tab**: File drag-and-drop uploader with quick test sample buttons.
- **Radial Quality Score Meter**: Color-coded gauge (`ACCEPTABLE` - Emerald, `DEGRADED` - Amber, `DEFECTIVE` - Rose).
- **Explainability Heatmap Inspector**: Toggle controls providing side-by-side or opacity-controlled overlay view of OpenCV Jet heatmaps.
- **Batch Processing Tab**: Multi-file batch uploader dashboard.
- **History Log**: Filterable/searchable analysis table linked to SQLite DB.
- **AI Benchmarks Dashboard**: Side-by-side RF and CNN metrics, confusion matrix, and feature importance rankings.

---

## 9. Performance, Concurrency & Monitoring

- **Asynchronous Threadpool Offloading**: Offloads all CPU-bound OpenCV decoding, feature extraction, and ML predictions to worker threadpools (`starlette.concurrency.run_in_threadpool`), keeping `asyncio` event loop latency under 2ms.
- **Multi-Worker Execution**: Configured with `UVICORN_WORKERS=4` in Dockerfile and Docker Compose.
- **Request Trace IDs**: Emits `X-Request-ID` headers and logs structured JSON entries (`timestamp`, `method`, `path`, `status`, `latency_ms`, `client_ip`).

---

## 10. Evaluation Results & Experimental Rigor

Tested on held-out test splits:

### Random Forest Model (14 CV Features)
- **Accuracy**: `87.92%`
- **Macro F1-Score**: `0.8812`
- **Sample Count**: 1,200 (240 test samples)
- **Uncertainty**: RF 120-tree decision agreement ratio (`tree_agreement`).

### DefectCNN Model (PyTorch ConvNet)
- **Accuracy**: `89.33%`
- **Macro F1-Score**: `0.8968`
- **Parameters**: 155,782 (CPU-optimized)
- **Sample Count**: 1,500 (300 test samples)

---

## 11. Installation & Deployment Instructions

### Local Execution (Step-by-Step)

1. **Backend Setup**:
   ```bash
   python3 -m venv backend/venv
   source backend/venv/bin/activate
   pip install -r backend/requirements.txt
   
   # Train RF and CNN models
   PYTHONPATH=. python backend/app/ml/train.py
   PYTHONPATH=. python backend/app/ml/train_cnn.py
   
   # Start Uvicorn backend server with 4 workers
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:3000` in your web browser.

---

## 12. Docker & Docker Compose Instructions

To build and run the full containerized stack:

```bash
docker-compose up --build
```

Services started:
- **Frontend SPA**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 13. Sample Test Images

Categorized test sample images are provided in both `samples/` and `backend/sample_images/`:

- `good_quality/sample_acceptable.png`: High-contrast, sharp image without defects.
- `medium_quality/sample_blur.png`: Gaussian defocus blur degradation.
- `medium_quality/sample_underexposure.png`: Underexposed dark image.
- `medium_quality/sample_overexposure.png`: Overexposed highlight blowout.
- `medium_quality/sample_noise.png`: Additive Gaussian noise grain.
- `poor_quality/sample_defective.png`: Scratches, dead pixel blocks, and color cast.
- `poor_quality/sample_corrupt.png`: Byte header corruption for file integrity testing.

---

## 14. Automated Testing & CI/CD

### Backend Pytest Suite (12 Tests Passed)
```bash
PYTHONPATH=. pytest backend/tests/ -v
```

### Frontend Vitest Suite (5 Test Suites Passed)
```bash
cd frontend && npm test
```

### High-Concurrency Load Benchmark
```bash
python backend/tests/load_test.py
```

### Continuous Integration (GitHub Actions)
Configured in [`.github/workflows/tests.yml`](file:///Users/balakrishnagunda/Desktop/iiith/.github/workflows/tests.yml) executing both Pytest and Vitest test suites on push/PR.

---

## 15. Troubleshooting Guide

- **Port 8000 or 3000 in use**: Stop existing services using `kill $(lsof -t -i:8000)` or change port in `.env`.
- **OpenCV `libGL.so.1` missing in Docker/Linux**: Installed automatically via `apt-get install -y libgl1-mesa-glx libglib2.0-0` in `Dockerfile`.
- **PyTorch installation memory limit**: The backend uses CPU-only PyTorch wheels (`--extra-index-url https://download.pytorch.org/whl/cpu`) to keep container builds fast and lightweight.
