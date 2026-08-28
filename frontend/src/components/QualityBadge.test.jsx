import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import QualityBadge from './QualityBadge';

describe('QualityBadge Component', () => {
  it('renders acceptable label and score correctly', () => {
    render(
      <QualityBadge
        score={94.5}
        label="ACCEPTABLE"
        explanation="Image exhibits excellent sharpness and low noise."
        mlConfidence={0.96}
      />
    );

    expect(screen.getByText('94.5')).toBeInTheDocument();
    expect(screen.getByText('ACCEPTABLE')).toBeInTheDocument();
    expect(screen.getByText(/excellent sharpness/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Model Confidence: 96%/i)).toBeInTheDocument();
  });

  it('renders degraded label badge styling', () => {
    render(
      <QualityBadge
        score={62.0}
        label="DEGRADED"
        explanation="Moderate underexposure detected."
        mlConfidence={0.82}
      />
    );

    expect(screen.getByText('62')).toBeInTheDocument();
    expect(screen.getByText('DEGRADED')).toBeInTheDocument();
    expect(screen.getByText(/Moderate underexposure/i)).toBeInTheDocument();
  });

  it('renders defective label badge styling', () => {
    render(
      <QualityBadge
        score={20.0}
        label="DEFECTIVE"
        explanation="Severe blur and structural corruption."
        mlConfidence={0.99}
      />
    );

    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('DEFECTIVE')).toBeInTheDocument();
  });
});
