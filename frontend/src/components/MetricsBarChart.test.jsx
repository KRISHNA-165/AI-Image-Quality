import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricsBarChart from './MetricsBarChart';

describe('MetricsBarChart Component', () => {
  it('renders all four score categories and raw metric details', () => {
    const rawMetrics = {
      laplacian_variance: 342.15,
      mean_brightness: 128.4,
      rms_contrast: 64.2,
      noise_sigma: 2.1,
      snr_db: 42.5
    };
    const scores = {
      sharpness_score: 95.0,
      brightness_score: 90.0,
      contrast_score: 85.0,
      noise_score: 8.0
    };

    render(<MetricsBarChart metrics={rawMetrics} scores={scores} />);

    expect(screen.getByText('Sharpness')).toBeInTheDocument();
    expect(screen.getByText('95.0 / 100')).toBeInTheDocument();
    expect(screen.getByText('Brightness Balance')).toBeInTheDocument();
    expect(screen.getByText('Contrast Range')).toBeInTheDocument();
    expect(screen.getByText('Noise Degradation')).toBeInTheDocument();
    expect(screen.getByText(/Laplacian Variance: 342.15/i)).toBeInTheDocument();
    expect(screen.getByText(/Mean Luminance: 128.4/i)).toBeInTheDocument();
  });
});
