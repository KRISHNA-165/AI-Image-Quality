import React from 'react';
import { BarChart3, Sun, Eye, Radio, Sparkles } from 'lucide-react';

export default function MetricsBarChart({ metrics }) {
  if (!metrics) return null;

  const norm = metrics.scores || {};
  const raw = metrics.raw || {};

  const metricList = [
    { label: 'Image Sharpness', score: norm.sharpness_score || 0, rawVal: `${raw.laplacian_variance || 0} (Lap Variance)`, icon: <Sparkles size={16} color="#6366f1" /> },
    { label: 'Exposure & Brightness', score: norm.brightness_score || 0, rawVal: `${raw.mean_brightness || 0} / 255 (Mean)`, icon: <Sun size={16} color="#f59e0b" /> },
    { label: 'Contrast & Dynamic Range', score: norm.contrast_score || 0, rawVal: `${raw.rms_contrast || 0} (RMS)`, icon: <Eye size={16} color="#3b82f6" /> },
    { label: 'Signal-to-Noise Ratio', score: Math.min(100, Math.max(0, (raw.snr_db || 0) * 2.5)), rawVal: `${raw.snr_db || 0} dB`, icon: <Radio size={16} color="#10b981" /> }
  ];

  return (
    <div className="glass-card" style={{ padding: '1.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BarChart3 size={18} color="var(--primary)" /> Vision Feature Metrics Breakdown
        </h4>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>0 - 100 Scale</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
        {metricList.map((m, idx) => (
          <div key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', marginBottom: '0.35rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: 'var(--text-main)' }}>
                {m.icon} {m.label}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                {m.rawVal}
              </span>
            </div>
            
            {/* Progress bar container */}
            <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, m.score))}%`,
                  height: '100%',
                  background: m.score >= 70 ? 'linear-gradient(90deg, #10b981, #34d399)' : (m.score >= 45 ? 'linear-gradient(90deg, #f59e0b, #fbbf24)' : 'linear-gradient(90deg, #f43f5e, #fb7185)'),
                  borderRadius: '4px',
                  transition: 'width 0.6s ease'
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Raw stats grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
        <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Underexposed Ratio</span>
          <strong style={{ fontSize: '0.85rem', color: '#f3f4f6' }}>{Math.round((raw.underexpose_ratio || 0) * 100)}%</strong>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Overexposed Ratio</span>
          <strong style={{ fontSize: '0.85rem', color: '#f3f4f6' }}>{Math.round((raw.overexpose_ratio || 0) * 100)}%</strong>
        </div>
        <div style={{ textAlign: 'center', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>Noise Sigma</span>
          <strong style={{ fontSize: '0.85rem', color: '#f3f4f6' }}>{raw.noise_sigma || 0}</strong>
        </div>
      </div>

    </div>
  );
}
