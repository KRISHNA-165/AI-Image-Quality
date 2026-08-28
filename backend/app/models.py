"""
SQLAlchemy Database Models.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, JSON, DateTime
from backend.app.database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    quality_score = Column(Float, nullable=False, index=True)
    quality_label = Column(String(50), nullable=False, index=True)  # ACCEPTABLE, DEGRADED, DEFECTIVE
    
    issues = Column(JSON, nullable=False)  # List of issue dicts
    metrics = Column(JSON, nullable=False) # Raw and normalized metrics
    explanation = Column(Text, nullable=True)
    
    image_url = Column(String(512), nullable=False)
    heatmap_url = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
