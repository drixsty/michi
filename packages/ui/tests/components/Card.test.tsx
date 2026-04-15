import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardBody, CardFooter } from '../../src/components/Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card><p>Contenu</p></Card>);
    expect(screen.getByText('Contenu')).toBeInTheDocument();
  });

  it('renders as a <div>', () => {
    const { container } = render(<Card>Test</Card>);
    expect(container.firstChild?.nodeName).toBe('DIV');
  });

  it('accepts elevated prop without crashing', () => {
    render(<Card elevated><p>Elevé</p></Card>);
    expect(screen.getByText('Elevé')).toBeInTheDocument();
  });
});

describe('CardHeader', () => {
  it('renders title', () => {
    render(<CardHeader title="Mon titre" />);
    expect(screen.getByText('Mon titre')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<CardHeader title="Titre" subtitle="Sous-titre" />);
    expect(screen.getByText('Sous-titre')).toBeInTheDocument();
  });

  it('does not render subtitle when omitted', () => {
    render(<CardHeader title="Titre" />);
    expect(screen.queryByText('Sous-titre')).toBeNull();
  });

  it('renders action slot', () => {
    render(<CardHeader title="Titre" action={<button>Action</button>} />);
    expect(screen.getByText('Action')).toBeInTheDocument();
  });
});

describe('CardBody', () => {
  it('renders children', () => {
    render(<CardBody><span>Corps</span></CardBody>);
    expect(screen.getByText('Corps')).toBeInTheDocument();
  });

  it('accepts noPadding prop without crashing', () => {
    render(<CardBody noPadding><span>NoPad</span></CardBody>);
    expect(screen.getByText('NoPad')).toBeInTheDocument();
  });
});

describe('CardFooter', () => {
  it('renders children', () => {
    render(<CardFooter><button>Annuler</button></CardFooter>);
    expect(screen.getByText('Annuler')).toBeInTheDocument();
  });
});

describe('Card composition', () => {
  it('renders full card with all sub-components', () => {
    render(
      <Card>
        <CardHeader title="Inventaire" subtitle="Mise à jour il y a 5 min" />
        <CardBody>
          <p>Contenu principal</p>
        </CardBody>
        <CardFooter>
          <button>Voir tout</button>
        </CardFooter>
      </Card>,
    );
    expect(screen.getByText('Inventaire')).toBeInTheDocument();
    expect(screen.getByText('Mise à jour il y a 5 min')).toBeInTheDocument();
    expect(screen.getByText('Contenu principal')).toBeInTheDocument();
    expect(screen.getByText('Voir tout')).toBeInTheDocument();
  });
});
