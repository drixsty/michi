import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../../src/components/Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Enregistrer</Button>);
    expect(screen.getByText('Enregistrer')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Cliquer</Button>);
    fireEvent.click(screen.getByText('Cliquer'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('does not call onClick when disabled', () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Désactivé</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('is disabled when loading', () => {
    render(<Button loading>Chargement</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders leftIcon slot', () => {
    render(<Button leftIcon={<span data-testid="icon">★</span>}>Avec icône</Button>);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('applies submit type', () => {
    render(<Button type="submit">Soumettre</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
  });

  it.each(['primary', 'secondary', 'ghost', 'destructive'] as const)(
    'renders variant=%s without crashing',
    (variant) => {
      render(<Button variant={variant}>Btn</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    },
  );

  it.each(['sm', 'md', 'lg'] as const)('renders size=%s without crashing', (size) => {
    render(<Button size={size}>Btn</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
