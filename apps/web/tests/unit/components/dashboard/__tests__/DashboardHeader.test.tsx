import { render, screen, fireEvent } from '@testing-library/react';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';

describe('DashboardHeader', () => {
  const defaultProps = {
    title: 'Test Title',
    subtitle: 'Test Subtitle',
    syncing: false,
    onSync: vi.fn(),
    onExport: vi.fn(),
  };

  it('renders title and subtitle correctly', () => {
    render(<DashboardHeader {...defaultProps} />);
    
    expect(screen.getByText('Test Title')).toBeInTheDocument();
    expect(screen.getByText('Test Subtitle')).toBeInTheDocument();
  });

  it('calls onSync when sync button is clicked', () => {
    render(<DashboardHeader {...defaultProps} />);
    
    const syncButton = screen.getByTestId('sync-button');
    fireEvent.click(syncButton);
    
    expect(defaultProps.onSync).toHaveBeenCalledTimes(1);
  });

  it('calls onExport when export button is clicked', () => {
    render(<DashboardHeader {...defaultProps} />);
    
    const exportButton = screen.getByTestId('export-button');
    fireEvent.click(exportButton);
    
    expect(defaultProps.onExport).toHaveBeenCalledTimes(1);
  });

  it('shows syncing state and disables button', () => {
    render(<DashboardHeader {...defaultProps} syncing={true} />);
    
    const syncButton = screen.getByTestId('sync-button');
    expect(screen.getByText('Synchronisation...')).toBeInTheDocument();
    expect(syncButton).toBeDisabled();
  });

  it('hides actions when showActions is false', () => {
    render(<DashboardHeader {...defaultProps} showActions={false} />);
    
    expect(screen.queryByTestId('sync-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('export-button')).not.toBeInTheDocument();
  });
});
