import React from 'react';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function IssueList({ issues = [] }) {
  if (!issues || issues.length === 0) {
    return (
      <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', background: 'rgba(16, 185, 129, 0.15)', padding: '0.75rem', borderRadius: '50%', color: '#10b981', marginBottom: '0.5rem' }}>
          <CheckCircle2 size={24} />
        </div>
        <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#34d399' }}>No Degradations Detected</h4>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>The uploaded image satisfies all visual quality benchmarks.</p>
      </div>
    );
  }

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return { bg: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', border: 'rgba(244, 63, 94, 0.3)', label: 'HIGH SEVERITY' };
      case 'medium':
        return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)', label: 'MEDIUM SEVERITY' };
      case 'low':
      default:
        return { bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)', label: 'LOW SEVERITY' };
    }
  };

  return (
    <div className="glass-card" style={{ padding: '1.75rem' }}>
      <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <ShieldAlert size={18} color="#f43f5e" /> Detected Quality Issues ({issues.length})
      </h4>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {issues.map((issue, idx) => {
          const sev = getSeverityBadge(issue.severity);
          return (
            <div
              key={idx}
              style={{
                background: 'rgba(0,0,0,0.25)',
                border: `1px solid ${sev.border}`,
                borderRadius: 'var(--radius-md)',
                padding: '1rem'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-main)' }}>
                  {issue.type.replace('_', ' ')}
                </span>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.7rem', fontWeight: 700, background: sev.bg, color: sev.color, border: `1px solid ${sev.border}`, padding: '0.15rem 0.5rem', borderRadius: '12px' }}>
                    {sev.label}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Conf: {Math.round(issue.confidence * 100)}%
                  </span>
                </div>
              </div>

              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                {issue.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
