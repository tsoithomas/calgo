import { render, screen } from '@testing-library/react';
import TradesTable from './TradesTable';

const mockTrades = [
  {
    symbol: 'AAPL',
    timestamp: '2026-03-13T20:45:00+00:00',
    side: 'buy',
    quantity: 10,
    price: 280.5,
  },
  {
    symbol: 'MSFT',
    timestamp: '2026-03-13T21:10:00+00:00',
    side: 'sell',
    quantity: 5,
    price: 415.0,
  },
];

describe('TradesTable', () => {
  it('renders column headers derived from trade fields', () => {
    render(<TradesTable trades={mockTrades} />);
    expect(screen.getByText('symbol')).toBeInTheDocument();
    expect(screen.getByText('timestamp')).toBeInTheDocument();
  });

  it('renders trade data rows', () => {
    render(<TradesTable trades={mockTrades} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('shows empty-state message when trades is null', () => {
    render(<TradesTable trades={null} />);
    expect(screen.getByText('No trades available')).toBeInTheDocument();
  });

  it('shows empty-state message when trades is undefined', () => {
    render(<TradesTable trades={undefined} />);
    expect(screen.getByText('No trades available')).toBeInTheDocument();
  });

  it('shows empty-state message when trades is empty array', () => {
    render(<TradesTable trades={[]} />);
    expect(screen.getByText('No trades available')).toBeInTheDocument();
  });

  it('does not render a table in empty state', () => {
    const { container } = render(<TradesTable trades={[]} />);
    expect(container.querySelector('table')).not.toBeInTheDocument();
  });

  it('handles trades with varying fields gracefully', () => {
    const mixedTrades = [
      { symbol: 'AAPL', timestamp: '2026-03-13T20:45:00+00:00', side: 'buy' },
      { symbol: 'MSFT', timestamp: '2026-03-13T21:10:00+00:00' },
    ];
    render(<TradesTable trades={mixedTrades} />);
    // Missing fields should render as em dash
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });
});
