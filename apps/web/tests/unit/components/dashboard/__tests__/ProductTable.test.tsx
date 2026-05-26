import { render, screen, fireEvent } from '@testing-library/react';
import { ProductTable } from '@/components/dashboard/ProductTable';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';

// Mock useRouter
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe('ProductTable', () => {
  const mockProducts = [
    {
      id: '1',
      sku: 'PROD-A',
      title: 'Product A',
      totalStock: 50,
      warningThreshold: 10,
      abcRank: 'A',
      channels: [{ platform: 'shopify' }]
    },
    {
      id: '2',
      sku: 'PROD-B',
      title: 'Product B',
      totalStock: 5,
      warningThreshold: 10,
      abcRank: 'B',
      channels: [{ platform: 'amazon' }]
    }
  ];

  it('renders products correctly', () => {
    render(<ProductTable products={mockProducts} />);
    
    expect(screen.getAllByText('Product A')[0]).toBeInTheDocument();
    expect(screen.getAllByText('PROD-A')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Product B')[0]).toBeInTheDocument();
  });

  it('filters products by search query', () => {
    render(<ProductTable products={mockProducts} query="Product A" />);
    
    expect(screen.getAllByText('Product A')[0]).toBeInTheDocument();
    expect(screen.queryByText('Product B')).not.toBeInTheDocument();
  });

  it('filters products by channel', () => {
    render(<ProductTable products={mockProducts} />);
    
    // Click on Amazon filter (p.charAt(0).toUpperCase() + p.slice(1) -> Amazon)
    const amazonButton = screen.getByText('Amazon');
    fireEvent.click(amazonButton);
    
    expect(screen.queryByText('Product A')).not.toBeInTheDocument();
    expect(screen.getAllByText('Product B')[0]).toBeInTheDocument();
  });

  it('renders empty state when no products match', () => {
    render(<ProductTable products={mockProducts} query="NonExistent" />);
    
    expect(screen.getAllByText('Données vides')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Aucun produit ne correspond à votre sélection.')[0]).toBeInTheDocument();
  });
});
