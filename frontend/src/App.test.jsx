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

    expect(screen.getByText('QualiVision AI')).toBeInTheDocument();
    expect(screen.getByText('Image Analyzer')).toBeInTheDocument();
    expect(screen.getByText('Batch Processing')).toBeInTheDocument();
    expect(screen.getByText('History Log')).toBeInTheDocument();
    expect(screen.getByText('AI Benchmarks')).toBeInTheDocument();
  });

  it('navigates to Batch Processing tab when clicked', async () => {
    render(<App />);

    const batchTab = screen.getByText('Batch Processing');
    fireEvent.click(batchTab);

    expect(screen.getByText(/Analyze multiple images simultaneously/i)).toBeInTheDocument();
  });

  it('navigates to AI Benchmarks tab when clicked', async () => {
    render(<App />);

    const benchmarksTab = screen.getByText('AI Benchmarks');
    fireEvent.click(benchmarksTab);

    await waitFor(() => {
      expect(screen.getByText(/AI Model Evaluation & Benchmarks/i)).toBeInTheDocument();
    });
  });
});
