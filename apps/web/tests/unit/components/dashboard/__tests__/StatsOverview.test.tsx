import { render, screen } from '@testing-library/react';
import { StatsOverview } from '../StatsOverview';
import { describe, it, expect } from 'vitest';
import React from 'react';

describe('StatsOverview', () => {
  const mockStats = {
    total: 100,
    urgent: 5,
    warning: 12,
    healthy: 83,
  };

  it('renders all 4 stat cards with correct values', () => {
    render(<StatsOverview stats={mockStats} />);
    
    expect(screen.getByText('Total produits')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    
    expect(screen.getByText('Ruptures critiques')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    
    expect(screen.getByText('À surveiller')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    
    expect(screen.getByText('Sains')).toBeInTheDocument();
    expect(screen.getByText('83')).toBeInTheDocument();
  });

  it('renders sub-labels correctly', () => {
    render(<StatsOverview stats={mockStats} />);
    
    expect(screen.getByText('Inventaire complet')).toBeInTheDocument();
    expect(screen.getByText('Rupture immédiate')).toBeInTheDocument();
    expect(screen.getByText('Stock < 20u.')).toBeInTheDocument();
    expect(screen.getByText('Stock optimisé')).toBeInTheDocument();
  });
});
