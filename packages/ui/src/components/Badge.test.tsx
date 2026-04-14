import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>En stock</Badge>);
    expect(screen.getByText('En stock')).toBeInTheDocument();
  });

  it.each(['default', 'primary', 'critical', 'warning', 'healthy', 'neutral'] as const)(
    'renders variant=%s without crashing',
    (variant) => {
      render(<Badge variant={variant}>{variant}</Badge>);
      expect(screen.getByText(variant)).toBeInTheDocument();
    },
  );

  it('accepts extra className', () => {
    render(<Badge className="custom-class">Test</Badge>);
    const el = screen.getByText('Test');
    expect(el).toHaveClass('custom-class');
  });

  it('renders as <span> element', () => {
    render(<Badge>Span</Badge>);
    expect(screen.getByText('Span').tagName).toBe('SPAN');
  });
});
