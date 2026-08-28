import React from 'react';
import { ShieldCheck, Cpu, History, Layers, Activity } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, healthStatus }) {
  return (
    <header className="glass-card" style={{ borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none', position: 'sticky', top: 0, zIndex: 50 }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ background: 'linear-gradient(135deg, #6366f1 0%, #10b981 100%)', padding: '0.6rem', borderRadius: '12px', display: 'flex' }}>
            <ShieldCheck size={26} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #9ca3af)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              QualiVision <span style={{ color: '#6366f1', WebkitTextFillColor: '#6366f1' }}>AI</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Visual Quality & Defect Detection Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.3rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`btn-secondary ${activeTab === 'analyzer' ? 'btn-primary' : ''}`}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: 'none' }}
          >
            <Activity size={16} /> Image Analyzer
          </button>

          <button
            onClick={() => setActiveTab('batch')}
            className={`btn-secondary ${activeTab === 'batch' ? 'btn-primary' : ''}`}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: 'none' }}
          >
            <Layers size={16} /> Batch Analysis
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`btn-secondary ${activeTab === 'history' ? 'btn-primary' : ''}`}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: 'none' }}
          >
            <History size={16} /> Analysis History
          </button>

          <button
            onClick={() => setActiveTab('benchmark')}
            className={`btn-secondary ${activeTab === 'benchmark' ? 'btn-primary' : ''}`}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', border: 'none' }}
          >
            <Cpu size={16} /> AI Benchmark & Metrics
          </button>
        </nav>

        {/* System Health Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.03)', padding: '0.4rem 0.8rem', borderRadius: '20px', border: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: healthStatus?.status === 'healthy' ? '#10b981' : '#f43f5e', display: 'inline-block', boxShadow: healthStatus?.status === 'healthy' ? '0 0 8px #10b981' : 'none' }}></span>
          <span style={{ color: '#d1d5db', fontWeight: 500 }}>
            {healthStatus?.status === 'healthy' ? 'AI Engine Ready' : 'Connecting...'}
          </span>
        </div>

      </div>
    </header>
  );
}
