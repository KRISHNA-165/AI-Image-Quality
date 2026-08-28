"""
Pydantic Schemas for Request & Response Data Transfer Objects.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class DetectedIssue(BaseModel):
    type: str = Field(..., description="Issue classification (e.g., blur, underexposure, noise, corruption)")
    severity: str = Field(..., description="Severity level: low, medium, high")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    description: Optional[str] = Field(None, description="Detailed explanation of the issue")

class AnalysisResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    quality_score: float = Field(..., description="Overall quality score from 0.0 to 100.0")
    quality_label: str = Field(..., description="Quality status label: ACCEPTABLE, DEGRADED, DEFECTIVE")
    issues: List[DetectedIssue]
    metrics: Dict[str, Any]
    explanation: str
    image_url: str
    heatmap_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedAnalysisResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[AnalysisResponse]

class BatchAnalysisResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    results: List[AnalysisResponse]

class ModelInfoResponse(BaseModel):
    model_loaded: bool
    model_version: Optional[str] = None
    trained_at: Optional[str] = None
    accuracy: Optional[float] = None
    f1_macro: Optional[float] = None
    classes: List[str] = []
    confusion_matrix: List[List[int]] = []
    feature_importances: Dict[str, float] = {}
    sample_count: Optional[int] = None
    cnn_model_loaded: bool = False
    cnn_accuracy: Optional[float] = None
    cnn_f1_macro: Optional[float] = None
    cnn_confusion_matrix: List[List[int]] = []
    cnn_architecture: Optional[str] = "DefectCNN (4-Layer PyTorch ConvNet, 64x64 input)"
    cnn_parameters: Optional[int] = None
