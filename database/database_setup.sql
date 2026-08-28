-- QualiVision AI — Database Schema Setup (SQLite DDL)
-- Note: SQLAlchemy automatically creates these tables on application launch if they do not exist.

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    quality_score FLOAT NOT NULL,
    quality_label VARCHAR(50) NOT NULL,
    issues JSON NOT NULL,
    metrics JSON NOT NULL,
    explanation TEXT,
    image_url VARCHAR(512) NOT NULL,
    heatmap_url VARCHAR(512),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_analysis_results_id ON analysis_results (id);
CREATE INDEX IF NOT EXISTS ix_analysis_results_quality_score ON analysis_results (quality_score);
CREATE INDEX IF NOT EXISTS ix_analysis_results_quality_label ON analysis_results (quality_label);
CREATE INDEX IF NOT EXISTS ix_analysis_results_created_at ON analysis_results (created_at);
