import React, { useState } from 'react';
import { Eye, Flame, Sliders, Layers } from 'lucide-react';

export default function ImageInspector({ imageUrl, heatmapUrl, filename }) {
  const [viewMode, setViewMode] = useState('heatmap'); // 'heatmap', 'side', 'original'
  const [opacity, setOpacity] = useState(0.85);

  if (!imageUrl) return null;

  return (
    <div className="glass-card" style={{ padding: '1.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Flame size={18} color="#f59e0b" /> Explainability & Defect Heatmap
          </h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{filename}</p>
        </div>

        {/* View Mode Toggle Controls */}
        <div style={{ display: 'flex', gap: '0.4rem', background: 'rgba(0,0,0,0.3)', padding: '0.25rem', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setViewMode('heatmap')}
            className={`btn-secondary ${viewMode === 'heatmap' ? 'btn-primary' : ''}`}
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', border: 'none' }}
          >
            <Flame size={14} /> Heatmap
          </button>
          <button
            onClick={() => setViewMode('side')}
            className={`btn-secondary ${viewMode === 'side' ? 'btn-primary' : ''}`}
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', border: 'none' }}
          >
            <Layers size={14} /> Side-by-Side
          </button>
          <button
            onClick={() => setViewMode('original')}
            className={`btn-secondary ${viewMode === 'original' ? 'btn-primary' : ''}`}
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', border: 'none' }}
          >
            <Eye size={14} /> Original
          </button>
        </div>
      </div>

      {/* Main Image Display Area */}
      <div style={{ background: '#030712', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', padding: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '320px', overflow: 'hidden' }}>
        
        {viewMode === 'heatmap' && heatmapUrl && (
          <div style={{ position: 'relative', maxWidth: '100%', borderRadius: '8px', overflow: 'hidden' }}>
            <img src={imageUrl} alt="Original" style={{ maxWidth: '100%', maxHeight: '420px', display: 'block', borderRadius: '8px' }} />
            <img
              src={heatmapUrl}
              alt="Heatmap Overlay"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                opacity: opacity,
                transition: 'opacity 0.2s ease',
                pointerEvents: 'none',
                borderRadius: '8px'
              }}
            />
          </div>
        )}

        {viewMode === 'side' && (
          <div style={{ display: 'grid', gridTemplateColumns: heatmapUrl ? '1fr 1fr' : '1fr', gap: '1rem', width: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Original Image</span>
              <img src={imageUrl} alt="Original" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain', borderRadius: '8px', border: '1px solid var(--border-color)' }} />
            </div>
            {heatmapUrl && (
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#f59e0b', display: 'block', marginBottom: '0.4rem' }}>Quality Anomaly Heatmap</span>
                <img src={heatmapUrl} alt="Heatmap" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)' }} />
              </div>
            )}
          </div>
        )}

        {viewMode === 'original' && (
          <img src={imageUrl} alt="Original Full" style={{ maxWidth: '100%', maxHeight: '420px', objectFit: 'contain', borderRadius: '8px' }} />
        )}

      </div>

      {/* Opacity slider for Heatmap view */}
      {viewMode === 'heatmap' && heatmapUrl && (
        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.02)', padding: '0.6rem 1rem', borderRadius: '8px' }}>
          <Sliders size={16} color="var(--text-muted)" />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Heatmap Overlay Opacity:</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={opacity}
            onChange={(e) => setOpacity(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: 'var(--primary)', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-main)', width: '35px' }}>{Math.round(opacity * 100)}%</span>
        </div>
      )}
    </div>
  );
}
