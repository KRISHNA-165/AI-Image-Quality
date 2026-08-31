import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { api } from './services/api';

vi.mock('./services/api', () => ({
  api: {
    healthCheck: vi.fn(),
    getModelInfo: vi.fn(),
    getAnalyses: vi.fn(),
    analyzeImage: vi.fn(),
    analyzeBatch: vi.fn()
  }
}));

describe('App Root Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.healthCheck.mockResolvedValue({ status: 'healthy' });
    api.getModelInfo.mockResolvedValue({
      model_loaded: true,
      accuracy: 0.88,
      f1_macro: 0.88,
      classes: [],
      confusion_matrix: [],
      feature_importances: {}
    });
    api.getAnalyses.mockResolvedValue({
      total: 0,
      page: 1,
      limit: 10,
      data: []
    });
  });

  it('renders application header and navigation tabs', async () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /QualiVision/i })).toBeInTheDocument();
    expect(screen.getByText('Image Analyzer')).toBeInTheDocument();
    expect(screen.getByText('Batch Analysis')).toBeInTheDocument();
    expect(screen.getByText('Analysis History')).toBeInTheDocument();
    expect(screen.getByText('AI Benchmark & Metrics')).toBeInTheDocument();
  });

  it('navigates to Batch Processing tab when clicked', async () => {
    render(<App />);

    const batchTab = screen.getByRole('button', { name: /Batch Analysis/i });
    fireEvent.click(batchTab);

    expect(screen.getByText(/Drag & Drop Multiple Images for Batch Analysis/i)).toBeInTheDocument();
  });

  it('navigates to AI Benchmarks tab when clicked', async () => {
    render(<App />);

    const benchmarksTab = screen.getByRole('button', { name: /AI Benchmark & Metrics/i });
    fireEvent.click(benchmarksTab);

    await waitFor(() => {
      expect(screen.getByText(/Evaluation Confusion Matrix/i)).toBeInTheDocument();
    });
  });
});
