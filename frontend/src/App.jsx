import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ImageUploader from './components/ImageUploader';
import QualityBadge from './components/QualityBadge';
import MetricsBarChart from './components/MetricsBarChart';
import IssueList from './components/IssueList';
import ImageInspector from './components/ImageInspector';
import AnalysisHistory from './components/AnalysisHistory';
import EvaluationDashboard from './components/EvaluationDashboard';
import { api } from './services/api';
import { Sparkles, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('analyzer');
  const [healthStatus, setHealthStatus] = useState(null);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [batchResults, setBatchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await api.healthCheck();
        setHealthStatus(res);
      } catch (err) {
        setHealthStatus({ status: 'error' });
      }
    }
    checkHealth();
  }, []);

  const handleAnalyzeSingleFile = async (file) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.analyzeImage(file);
      setCurrentAnalysis(res);
    } catch (err) {
      console.error("Analysis failed:", err);
      setErrorMsg(err.response?.data?.detail || "Failed to analyze image.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeBatchFiles = async (files) => {
    if (!files || files.length === 0) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.analyzeBatch(files);
      setBatchResults(res);
    } catch (err) {
      console.error("Batch analysis failed:", err);
      setErrorMsg(err.response?.data?.detail || "Batch analysis failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestSample = async (sampleName) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      // Fetch sample image from sample static path
      const sampleUrl = `/storage/../sample_images/sample_${sampleName}.png`;
      const response = await fetch(sampleUrl);
      if (!response.ok) {
        throw new Error(`Failed to load sample image sample_${sampleName}.png`);
      }
      const blob = await response.blob();
      const file = new File([blob], `sample_${sampleName}.png`, { type: 'image/png' });
      await handleAnalyzeSingleFile(file);
    } catch (err) {
      setErrorMsg(`Could not load sample image: ${err.message}`);
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} healthStatus={healthStatus} />

      <main style={{ maxWidth: '1280px', width: '100%', margin: '0 auto', padding: '2rem 1.5rem', flex: 1 }}>
        
        {/* Error Notification Banner */}
        {errorMsg && (
          <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fb7185', padding: '1rem 1.25rem', borderRadius: '12px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <AlertCircle size={20} />
            <span style={{ fontSize: '0.85rem', flex: 1 }}>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} style={{ background: 'transparent', border: 'none', color: '#fb7185', cursor: 'pointer', fontWeight: 700 }}>✕</button>
          </div>
        )}

        {/* TAB 1: SINGLE IMAGE ANALYZER */}
        {activeTab === 'analyzer' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            {/* Quick Sample Selector Bar */}
            <div className="glass-card" style={{ padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                <Sparkles size={16} color="var(--primary)" />
                <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>Quick Sample Test:</span> Click to evaluate pre-configured defect conditions:
              </div>

              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                {['acceptable', 'blur', 'underexposure', 'overexposure', 'noise', 'defective'].map((sample) => (
                  <button
                    key={sample}
                    onClick={() => handleTestSample(sample)}
                    disabled={isLoading}
                    className="btn-secondary"
                    style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', textTransform: 'capitalize' }}
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>

            {/* Uploader Box */}
            <ImageUploader onSelectFile={handleAnalyzeSingleFile} isLoading={isLoading} />

            {/* Results Display Section */}
            {currentAnalysis && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                
                {/* Top Row: Quality Gauge & Metrics Breakdown */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
                  <QualityBadge
                    score={currentAnalysis.quality_score}
                    label={currentAnalysis.quality_label}
                    explanation={currentAnalysis.explanation}
                    mlConfidence={currentAnalysis.metrics?.ml_confidence}
                  />

                  <MetricsBarChart metrics={currentAnalysis.metrics} />
                </div>

                {/* Middle Row: Issues List & Inspector */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
                  <IssueList issues={currentAnalysis.issues} />

                  <ImageInspector
                    imageUrl={currentAnalysis.image_url}
                    heatmapUrl={currentAnalysis.heatmap_url}
                    filename={currentAnalysis.original_filename}
                  />
                </div>

              </div>
            )}

          </div>
        )}

        {/* TAB 2: BATCH PROCESSING */}
        {activeTab === 'batch' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <ImageUploader isBatch={true} onSelectBatchFiles={handleAnalyzeBatchFiles} isLoading={isLoading} />

            {batchResults && (
              <div className="glass-card" style={{ padding: '2rem' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckCircle2 size={20} /> Batch Processing Complete
                </h3>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                  Processed {batchResults.total_processed} images ({batchResults.successful} successful, {batchResults.failed} failed).
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.25rem' }}>
                  {batchResults.results.map((res) => (
                    <div
                      key={res.id}
                      onClick={() => { setCurrentAnalysis(res); setActiveTab('analyzer'); }}
                      className="glass-card"
                      style={{ padding: '1rem', cursor: 'pointer' }}
                    >
                      <img src={res.image_url} alt="Batch Preview" style={{ width: '100%', height: 140, objectFit: 'cover', borderRadius: '8px', marginBottom: '0.75rem' }} />
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '160px' }}>
                          {res.original_filename}
                        </span>
                        <span style={{ fontSize: '0.9rem', fontWeight: 800 }}>{res.quality_score}</span>
                      </div>
                      <span className={`badge-${res.quality_label.toLowerCase()}`} style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: '8px', fontWeight: 700 }}>
                        {res.quality_label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: HISTORY LOG */}
        {activeTab === 'history' && (
          <AnalysisHistory
            onSelectRecord={(rec) => {
              setCurrentAnalysis(rec);
              setActiveTab('analyzer');
            }}
          />
        )}

        {/* TAB 4: BENCHMARK DASHBOARD */}
        {activeTab === 'benchmark' && (
          <EvaluationDashboard />
        )}

      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '1.5rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.3)' }}>
        QualiVision AI — Production Image Quality & Defect Detection Engine • Computer Vision & Hybrid Machine Learning
      </footer>
    </div>
  );
}
