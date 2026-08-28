import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import IssueList from './IssueList';

describe('IssueList Component', () => {
  it('renders clean state when no issues detected', () => {
    render(<IssueList issues={[]} />);
    expect(screen.getByText(/No Quality Defects Detected/i)).toBeInTheDocument();
    expect(screen.getByText(/passed all sharpness, exposure, and noise thresholds/i)).toBeInTheDocument();
  });

  it('renders list of detected quality issues with severity and confidence', () => {
    const issues = [
      {
        type: 'blur',
        severity: 'high',
        confidence: 0.94,
        description: 'Insufficient image sharpness (Laplacian variance: 8.5)'
      },
      {
        type: 'noise',
        severity: 'medium',
        confidence: 0.80,
        description: 'Elevated high-frequency background grain'
      }
    ];

    render(<IssueList issues={issues} />);
    expect(screen.getByText(/Identified Quality Issues \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText('BLUR')).toBeInTheDocument();
    expect(screen.getByText('HIGH Severity')).toBeInTheDocument();
    expect(screen.getByText(/94% Conf/i)).toBeInTheDocument();
    expect(screen.getByText('NOISE')).toBeInTheDocument();
    expect(screen.getByText(/Elevated high-frequency background grain/i)).toBeInTheDocument();
  });
});
