"""
FastAPI REST API Routes.
Provides asynchronous, non-blocking image evaluation, batch analysis,
telemetry metrics, model diagnostic inspection, and analysis history.
"""

import os
import uuid
import logging
import asyncio
import cv2
import numpy as np
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from backend.app.database import get_db, SessionLocal
from backend.app.models import AnalysisResult
from backend.app.schemas import (
    AnalysisResponse, PaginatedAnalysisResponse, BatchAnalysisResponse, ModelInfoResponse
)
from backend.app.config import settings
from backend.app.vision.corrupt_detector import check_file_integrity, analyze_corruption_features
from backend.app.vision.extractor import extract_image_features
from backend.app.vision.heatmaps import generate_quality_heatmap
from backend.app.ml.evaluator import QualityEvaluator
from backend.app.metrics import metrics_collector

router = APIRouter()
logger = logging.getLogger(__name__)
evaluator = QualityEvaluator()


def _process_image_cpu(file_bytes: bytes, filename: str):
    """
    Synchronous CPU-bound pipeline function for threadpool execution.
    Executes OpenCV decoding, feature extraction, corruption analysis, ML evaluation, and heatmap generation.
    """
    unique_id = str(uuid.uuid4())[:8]
    saved_filename = f"{unique_id}_{filename}"
    upload_path = os.path.join(settings.UPLOADS_DIR, saved_filename)
    heatmap_path = os.path.join(settings.HEATMAPS_DIR, f"heatmap_{saved_filename}")

    # 1. Byte-level integrity check
    is_valid, err_msg, meta = check_file_integrity(file_bytes)
    with open(upload_path, "wb") as f:
        f.write(file_bytes)

    if not is_valid:
        return {
            "saved_filename": saved_filename,
            "file_size": len(file_bytes),
            "width": 0,
            "height": 0,
            "quality_score": 0.0,
            "quality_label": "DEFECTIVE",
            "issues": [{
                "type": "corruption",
                "severity": "high",
                "confidence": 0.99,
                "description": err_msg or "Corrupt file header or unreadable pixel stream"
            }],
            "metrics": {"corruption": True, "error": err_msg},
            "explanation": f"Image rejected: {err_msg}",
            "heatmap_url": None,
        }

    # 2. Decode image pixels
    img_np = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img_np is None:
        return {
            "saved_filename": saved_filename,
            "file_size": len(file_bytes),
            "width": 0,
            "height": 0,
            "quality_score": 0.0,
            "quality_label": "DEFECTIVE",
            "issues": [{
                "type": "corruption",
                "severity": "high",
                "confidence": 0.99,
                "description": "OpenCV failed to decode image pixels"
            }],
            "metrics": {"corruption": True},
            "explanation": "Failed to decode pixel buffer.",
            "heatmap_url": None,
        }

    h, w = img_np.shape[:2]

    # 3. Vision feature extraction & corruption analysis
    corrupt_info = analyze_corruption_features(img_np)
    feat_dict = extract_image_features(img_np)

    # 4. ML Ensemble Inference
    eval_result = evaluator.evaluate(feat_dict, corrupt_info, img_bgr=img_np)

    # 5. Defect Heatmap Generation
    primary_issue_type = eval_result["issues"][0]["type"] if eval_result["issues"] else "general"
    try:
        heatmap_np = generate_quality_heatmap(img_np, defect_type=primary_issue_type)
        cv2.imwrite(heatmap_path, heatmap_np)
        heatmap_url = f"/storage/heatmaps/heatmap_{saved_filename}"
    except Exception as e:
        logger.error(f"Heatmap generation failed: {e}")
        heatmap_url = None

    full_metrics = {
        "raw": feat_dict["raw_metrics"],
        "scores": feat_dict["normalized_scores"],
        "corruption_analysis": corrupt_info,
        "predicted_class": eval_result.get("predicted_class"),
        "ml_confidence": eval_result.get("ml_confidence"),
        "cnn_prediction": eval_result.get("cnn_prediction"),
        "uncertainty": eval_result.get("uncertainty"),
        "ml_ensemble": {
            "predicted_class": eval_result.get("predicted_class"),
            "confidence": eval_result.get("ml_confidence"),
            "cnn_engaged": eval_result.get("cnn_prediction") is not None,
        }
    }

    return {
        "saved_filename": saved_filename,
        "file_size": len(file_bytes),
        "width": w,
        "height": h,
        "quality_score": eval_result["quality_score"],
        "quality_label": eval_result["quality_label"],
        "issues": eval_result["issues"],
        "metrics": full_metrics,
        "explanation": eval_result["explanation"],
        "heatmap_url": heatmap_url,
    }


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an image file for quality & defect analysis.
    Offloads CPU-bound CV & ML operations to worker threadpool to prevent event loop blocking.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Offload CPU-heavy computation to threadpool
    processed = await run_in_threadpool(_process_image_cpu, file_bytes, file.filename)

    record = AnalysisResult(
        filename=processed["saved_filename"],
        original_filename=file.filename,
        file_size=processed["file_size"],
        width=processed["width"],
        height=processed["height"],
        quality_score=processed["quality_score"],
        quality_label=processed["quality_label"],
        issues=processed["issues"],
        metrics=processed["metrics"],
        explanation=processed["explanation"],
        image_url=f"/storage/uploads/{processed['saved_filename']}",
        heatmap_url=processed["heatmap_url"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Record telemetry business metrics
    metrics_collector.record_analysis(record.quality_label, record.issues)

    return record


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Concurrent batch analysis endpoint for processing up to 20 images in parallel.
    Uses asyncio.gather and bounded concurrency to maximize CPU utilization.
    """
    if not files or len(files) > 20:
        raise HTTPException(status_code=400, detail="Batch request must contain between 1 and 20 files")

    # Read all file bytes asynchronously first
    file_payloads = []
    for f in files:
        b = await f.read()
        if b:
            file_payloads.append((b, f.filename))

    semaphore = asyncio.Semaphore(8)

    async def _process_single(file_bytes: bytes, filename: str):
        async with semaphore:
            return await run_in_threadpool(_process_image_cpu, file_bytes, filename)

    tasks = [_process_single(b, name) for b, name in file_payloads]
    processed_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    successful = 0
    failed = 0

    for i, res in enumerate(processed_results):
        if isinstance(res, Exception):
            failed += 1
            logger.error(f"Batch item failed for {file_payloads[i][1]}: {res}")
            continue

        record = AnalysisResult(
            filename=res["saved_filename"],
            original_filename=file_payloads[i][1],
            file_size=res["file_size"],
            width=res["width"],
            height=res["height"],
            quality_score=res["quality_score"],
            quality_label=res["quality_label"],
            issues=res["issues"],
            metrics=res["metrics"],
            explanation=res["explanation"],
            image_url=f"/storage/uploads/{res['saved_filename']}",
            heatmap_url=res["heatmap_url"],
        )
        db.add(record)
        results.append(record)
        successful += 1
        metrics_collector.record_analysis(record.quality_label, record.issues)

    if successful > 0:
        db.commit()
        for r in results:
            db.refresh(r)

    return {
        "total_processed": len(files),
        "successful": successful,
        "failed": failed,
        "results": results
    }


@router.get("/analyses", response_model=PaginatedAnalysisResponse)
def get_analyses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    label: Optional[str] = Query(None, description="Filter by quality label: ACCEPTABLE, DEGRADED, DEFECTIVE"),
    search: Optional[str] = Query(None, description="Search by original filename"),
    db: Session = Depends(get_db)
):
    """Retrieve history of past image analysis results with pagination and filtering."""
    query = db.query(AnalysisResult)

    if label:
        query = query.filter(AnalysisResult.quality_label == label.upper())

    if search:
        query = query.filter(AnalysisResult.original_filename.ilike(f"%{search}%"))

    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(AnalysisResult.created_at)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": results
    }


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis_by_id(analysis_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single analysis record by ID."""
    result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Analysis record with ID {analysis_id} not found")
    return result


@router.delete("/analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete an analysis record and remove its stored images."""
    result = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f"Analysis record with ID {analysis_id} not found")

    # Clean up file artifacts
    upload_file_path = os.path.join(settings.BASE_DIR, result.image_url.lstrip("/"))
    if os.path.exists(upload_file_path):
        try:
            os.remove(upload_file_path)
        except Exception:
            pass

    if result.heatmap_url:
        heatmap_file_path = os.path.join(settings.BASE_DIR, result.heatmap_url.lstrip("/"))
        if os.path.exists(heatmap_file_path):
            try:
                os.remove(heatmap_file_path)
            except Exception:
                pass

    db.delete(result)
    db.commit()
    return None


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive service health, memory footprint, and model status check."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    snapshot = metrics_collector.get_metrics_snapshot()

    return {
        "status": "healthy" if db_status == "connected" and evaluator.is_loaded else "degraded",
        "database": db_status,
        "uptime_seconds": snapshot["uptime_seconds"],
        "memory_mb": snapshot["system"]["process_memory_mb"],
        "model_loaded": evaluator.is_loaded,
        "cnn_loaded": evaluator.cnn.is_loaded,
        "cnn_model_loaded": evaluator.cnn.is_loaded,
        "available_classes": evaluator.classes,
        "total_requests_served": snapshot["http"]["total_requests"]
    }


@router.get("/metrics")
def get_metrics():
    """Real-time observability endpoint with latency distributions and throughput metrics."""
    return metrics_collector.get_metrics_snapshot()


@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info():
    """Retrieve AI model evaluation metrics: RF classifier + CNN ensemble."""
    rf_metrics = evaluator.metrics_info
    cnn_metrics = evaluator.cnn.metrics_info

    return {
        "model_loaded": evaluator.is_loaded,
        "model_version": rf_metrics.get("model_version"),
        "trained_at": rf_metrics.get("trained_at"),
        "accuracy": rf_metrics.get("accuracy"),
        "f1_macro": rf_metrics.get("f1_macro"),
        "classes": rf_metrics.get("classes", []),
        "confusion_matrix": rf_metrics.get("confusion_matrix", []),
        "feature_importances": rf_metrics.get("feature_importances", {}),
        "sample_count": rf_metrics.get("sample_count"),
        "cnn_model_loaded": evaluator.cnn.is_loaded,
        "cnn_accuracy": cnn_metrics.get("accuracy"),
        "cnn_f1_macro": cnn_metrics.get("f1_macro"),
        "cnn_confusion_matrix": cnn_metrics.get("confusion_matrix", []),
        "cnn_architecture": "DefectCNN (4-Layer PyTorch ConvNet, 64x64 input)",
        "cnn_parameters": cnn_metrics.get("num_parameters"),
    }
