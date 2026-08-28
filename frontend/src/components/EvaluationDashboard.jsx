import React, { useState, useEffect } from 'react';
import { Cpu, Award, BarChart, CheckCircle, Database } from 'lucide-react';
import { api } from '../services/api';

export default function EvaluationDashboard() {
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMetrics() {
      try {
        const info = await api.getModelInfo();
        setModelInfo(info);
      } catch (err) {
        console.error("Failed to load model info:", err);
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading AI model evaluation metrics...</p>
      </div>
    );
  }

  if (!modelInfo) return null;

  const classes = modelInfo.classes || ["ACCEPTABLE", "BLUR", "UNDEREXPOSURE", "OVEREXPOSURE", "NOISE", "DEFECTIVE"];
  const matrix = modelInfo.confusion_matrix || [];
  const featureImportances = modelInfo.feature_importances || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Top Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '0.85rem', borderRadius: '12px', color: '#10b981' }}>
            <Award size={28} />
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>RF Test Accuracy</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399' }}>
              {modelInfo.accuracy ? Math.round(modelInfo.accuracy * 100) : '—'}%
            </h3>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '0.85rem', borderRadius: '12px', color: '#6366f1' }}>
            <Cpu size={28} />
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>RF Macro F1</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#818cf8' }}>
              {modelInfo.f1_macro ?? '—'}
            </h3>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '0.85rem', borderRadius: '12px', color: '#f59e0b' }}>
            <Database size={28} />
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>RF Dataset</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24' }}>
              {modelInfo.sample_count || '—'}
            </h3>
          </div>
        </div>

        {/* CNN Metrics */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(236, 72, 153, 0.15)', padding: '0.85rem', borderRadius: '12px', color: '#ec4899' }}>
            <Cpu size={28} />
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>CNN Accuracy</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f472b6' }}>
              {modelInfo.cnn_accuracy ? Math.round(modelInfo.cnn_accuracy * 100) : '—'}%
            </h3>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ background: 'rgba(236, 72, 153, 0.15)', padding: '0.85rem', borderRadius: '12px', color: '#ec4899' }}>
            <Award size={28} />
          </div>
          <div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>CNN Params</span>
            <h3 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f472b6' }}>
              {modelInfo.cnn_parameters ? `${(modelInfo.cnn_parameters / 1000).toFixed(1)}K` : '—'}
            </h3>
          </div>
        </div>
      </div>

      {/* Main Grid: Confusion Matrix & Feature Importances */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
        
        {/* Confusion Matrix Card */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart size={18} color="var(--primary)" /> Evaluation Confusion Matrix
          </h4>

          {matrix.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', textAlign: 'center' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>Actual \ Predicted</th>
                    {classes.map((cls, i) => (
                      <th key={i} style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>{cls.substring(0, 4)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.map((row, rIdx) => (
                    <tr key={rIdx}>
                      <td style={{ padding: '0.5rem', fontWeight: 700, textAlign: 'left', color: 'var(--text-main)' }}>
                        {classes[rIdx]}
                      </td>
                      {row.map((val, cIdx) => (
                        <td
                          key={cIdx}
                          style={{
                            padding: '0.6rem',
                            fontWeight: 700,
                            background: rIdx === cIdx ? 'rgba(16, 185, 129, 0.25)' : (val > 0 ? 'rgba(244, 63, 94, 0.2)' : 'rgba(255,255,255,0.02)'),
                            color: rIdx === cIdx ? '#34d399' : (val > 0 ? '#fb7185' : 'var(--text-dim)'),
                            borderRadius: '4px'
                          }}
                        >
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Confusion matrix data available post training run.</p>
          )}
        </div>

        {/* Feature Importance Rankings */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} color="#10b981" /> Top Computer Vision Feature Importances
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {Object.entries(featureImportances)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 6)
              .map(([feat, imp], idx) => (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{feat}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{Math.round(imp * 100)}%</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${Math.round(imp * 100)}%`, height: '100%', background: 'var(--primary)', borderRadius: '3px' }} />
                  </div>
                </div>
              ))}
          </div>
        </div>

      </div>

    </div>
  );
}
