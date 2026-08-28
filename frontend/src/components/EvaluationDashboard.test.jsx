import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import EvaluationDashboard from './EvaluationDashboard';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getModelInfo: vi.fn()
  }
}));

describe('EvaluationDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    api.getModelInfo.mockReturnValue(new Promise(() => {}));
    render(<EvaluationDashboard />);
    expect(screen.getByText(/Loading AI model evaluation metrics/i)).toBeInTheDocument();
  });

  it('renders model evaluation metrics and confusion matrix after API resolves', async () => {
    api.getModelInfo.mockResolvedValue({
      model_loaded: true,
      accuracy: 0.88,
      f1_macro: 0.88,
      sample_count: 1200,
      cnn_model_loaded: true,
      cnn_accuracy: 0.91,
      cnn_parameters: 155782,
      classes: ['ACCEPTABLE', 'BLUR', 'DEFECTIVE'],
      confusion_matrix: [
        [35, 3, 2],
        [4, 34, 2],
        [1, 2, 37]
      ],
      feature_importances: {
        laplacian_var: 0.12,
        mean_brightness: 0.10
      }
    });

    render(<EvaluationDashboard />);

    await waitFor(() => {
      expect(screen.getByText('88%')).toBeInTheDocument();
      expect(screen.getByText('91%')).toBeInTheDocument();
      expect(screen.getByText('155.8K')).toBeInTheDocument();
      expect(screen.getByText('1200')).toBeInTheDocument();
      expect(screen.getByText('laplacian_var')).toBeInTheDocument();
      expect(screen.getByText(/Evaluation Confusion Matrix/i)).toBeInTheDocument();
    });
  });
});
