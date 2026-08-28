import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Award } from 'lucide-react';

export default function QualityBadge({ score, label, explanation, mlConfidence }) {
  const getLabelTheme = (lbl) => {
    switch (lbl?.toUpperCase()) {
      case 'ACCEPTABLE':
        return {
          badgeClass: 'badge-acceptable',
          icon: <CheckCircle2 size={20} />,
          color: '#10b981',
          gradient: 'conic-gradient(#10b981 ' + score + '%, rgba(255,255,255,0.08) 0)'
        };
      case 'DEGRADED':
        return {
          badgeClass: 'badge-degraded',
          icon: <AlertTriangle size={20} />,
          color: '#f59e0b',
          gradient: 'conic-gradient(#f59e0b ' + score + '%, rgba(255,255,255,0.08) 0)'
        };
      case 'DEFECTIVE':
      default:
        return {
          badgeClass: 'badge-defective',
          icon: <XCircle size={20} />,
          color: '#f43f5e',
          gradient: 'conic-gradient(#f43f5e ' + score + '%, rgba(255,255,255,0.08) 0)'
        };
    }
  };

  const theme = getLabelTheme(label);

  return (
    <div className="glass-card" style={{ padding: '1.75rem', textAlign: 'center', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      
      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '1.25rem' }}>
        Overall Quality Assessment
      </p>

      {/* Radial Gauge */}
      <div style={{ position: 'relative', width: 140, height: 140, borderRadius: '50%', background: theme.gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem', padding: 8 }}>
        <div style={{ width: '100%', height: '100%', background: '#0f172a', borderRadius: '50%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '2.4rem', fontWeight: 800, color: theme.color, lineHeight: 1 }}>
            {score}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ 100</span>
        </div>
      </div>

      {/* Status Badge Pill */}
      <div className={`badge ${theme.badgeClass}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1.25rem', borderRadius: '25px', fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem' }}>
        {theme.icon}
        <span>{label}</span>
      </div>

      {/* Explanation text */}
      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '320px', lineHeight: 1.4, margin: '0 auto' }}>
        {explanation}
      </p>

      {mlConfidence && (
        <div style={{ marginTop: '1rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.03)', padding: '0.25rem 0.75rem', borderRadius: '12px' }}>
          <Award size={14} color="var(--primary)" /> AI Model Confidence: {Math.round(mlConfidence * 100)}%
        </div>
      )}
    </div>
  );
}
