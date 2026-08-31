import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricsBarChart from './MetricsBarChart';

describe('MetricsBarChart Component', () => {
  it('renders all four score categories and raw metric details', () => {
    const metrics = {
      raw: {
        laplacian_variance: 342.15,
        mean_brightness: 128.4,
        rms_contrast: 64.2,
        noise_sigma: 2.1,
        snr_db: 42.5
      },
      scores: {
        sharpness_score: 95.0,
        brightness_score: 90.0,
        contrast_score: 85.0,
        noise_score: 8.0
      }
    };

    render(<MetricsBarChart metrics={metrics} />);

    expect(screen.getByText('Image Sharpness')).toBeInTheDocument();
    expect(screen.getByText('Exposure & Brightness')).toBeInTheDocument();
    expect(screen.getByText('Contrast & Dynamic Range')).toBeInTheDocument();
    expect(screen.getByText('Signal-to-Noise Ratio')).toBeInTheDocument();
    expect(screen.getByText('342.15 (Lap Variance)')).toBeInTheDocument();
    expect(screen.getByText('128.4 / 255 (Mean)')).toBeInTheDocument();
  });
});
