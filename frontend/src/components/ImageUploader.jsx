import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, Sparkles, AlertCircle, FileCheck } from 'lucide-react';

export default function ImageUploader({ onSelectFile, isLoading, isBatch = false, onSelectBatchFiles }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedPreview, setSelectedPreview] = useState(null);
  const [fileCount, setFileCount] = useState(0);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFiles(Array.from(e.target.files));
    }
  };

  const processFiles = (files) => {
    if (isBatch) {
      const validFiles = files.filter(f => f.type.startsWith('image/'));
      setFileCount(validFiles.length);
      onSelectBatchFiles(validFiles);
    } else {
      const singleFile = files[0];
      if (singleFile) {
        setSelectedPreview(URL.createObjectURL(singleFile));
        onSelectFile(singleFile);
      }
    }
  };

  return (
    <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${dragActive ? 'var(--primary)' : 'rgba(255, 255, 255, 0.15)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '3rem 2rem',
          background: dragActive ? 'rgba(99, 102, 241, 0.08)' : 'rgba(0, 0, 0, 0.2)',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          position: 'relative'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/bmp"
          multiple={isBatch}
          style={{ display: 'none' }}
          onChange={handleChange}
        />

        <div style={{ display: 'inline-flex', background: 'rgba(99, 102, 241, 0.15)', padding: '1.25rem', borderRadius: '50%', marginBottom: '1rem', color: 'var(--primary)' }}>
          <UploadCloud size={38} />
        </div>

        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          {isBatch ? 'Drag & Drop Multiple Images for Batch Analysis' : 'Upload an Image for Quality Analysis'}
        </h3>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 1.5rem auto' }}>
          {isBatch
            ? 'Select up to 20 images to process simultaneously in batch mode.'
            : 'Supports JPEG, PNG, WEBP, and BMP format up to 25MB.'}
        </p>

        {selectedPreview && !isBatch && (
          <div style={{ display: 'inline-block', position: 'relative', marginTop: '0.5rem', marginBottom: '1rem', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--border-highlight)' }}>
            <img src={selectedPreview} alt="Upload Preview" style={{ maxHeight: '160px', objectFit: 'contain', display: 'block' }} />
          </div>
        )}

        {isBatch && fileCount > 0 && (
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.85rem' }}>
            <FileCheck size={16} /> {fileCount} images selected for batch processing
          </div>
        )}

        <div>
          <button className="btn-primary" disabled={isLoading} style={{ margin: '0 auto' }}>
            {isLoading ? (
              <>
                <div className="spinner" style={{ border: '2px solid transparent', borderTop: '2px solid white', borderRadius: '50%', width: 16, height: 16 }}></div>
                Analyzing Computer Vision & AI Features...
              </>
            ) : (
              <>
                <Sparkles size={18} /> {isBatch ? 'Analyze Batch Images' : 'Choose File or Drag Here'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
