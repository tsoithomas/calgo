import { render, screen } from '@testing-library/react';
import PriceChart from './PriceChart';

const mockRecords = [
  { timestamp: '2025-12-04T00:00:00', open: '284.0950', high: '284.7300', low: '278.5900', close: '280.7000', volume: 43989056 },
  { timestamp: '2025-12-05T00:00:00', open: '281.0000', high: '285.0000', low: '279.0000', close: '283.5000', volume: 38000000 },
];

describe('PriceChart', () => {
  it('renders a recharts container when data is provided', () => {
    const { container } = render(<PriceChart data={{ symbol: 'AAPL', records: mockRecords }} symbol="AAPL" />);
    // ResponsiveContainer renders a div wrapper; verify the chart container is present
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('renders chart without empty-state when data is provided', () => {
    const { container } = render(<PriceChart data={{ symbol: 'AAPL', records: mockRecords }} symbol="AAPL" />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    expect(screen.queryByText(/No price data/)).not.toBeInTheDocument();
  });

  it('shows empty-state message when data is null', () => {
    render(<PriceChart data={null} symbol="AAPL" />);
    expect(screen.getByText('No price data available for AAPL')).toBeInTheDocument();
  });

  it('shows empty-state message when data is undefined', () => {
    render(<PriceChart data={undefined} symbol="MSFT" />);
    expect(screen.getByText('No price data available for MSFT')).toBeInTheDocument();
  });

  it('shows empty-state message when records array is empty', () => {
    render(<PriceChart data={{ symbol: 'GOOGL', records: [] }} symbol="GOOGL" />);
    expect(screen.getByText('No price data available for GOOGL')).toBeInTheDocument();
  });

  it('does not render svg in empty state', () => {
    render(<PriceChart data={null} symbol="AAPL" />);
    expect(document.querySelector('svg')).not.toBeInTheDocument();
  });
});
