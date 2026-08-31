import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import IssueList from './IssueList';

describe('IssueList Component', () => {
  it('renders clean state when no issues detected', () => {
    render(<IssueList issues={[]} />);
    expect(screen.getByText(/No Degradations Detected/i)).toBeInTheDocument();
    expect(screen.getByText(/satisfies all visual quality benchmarks/i)).toBeInTheDocument();
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
    expect(screen.getByRole('heading', { name: /Detected Quality Issues/i })).toBeInTheDocument();
    expect(screen.getByText(/blur/i)).toBeInTheDocument();
    expect(screen.getByText('HIGH SEVERITY')).toBeInTheDocument();
    expect(screen.getByText(/Conf:\s*94\s*%/i)).toBeInTheDocument();
    expect(screen.getByText(/noise/i)).toBeInTheDocument();
    expect(screen.getByText(/Elevated high-frequency background grain/i)).toBeInTheDocument();
  });
});
