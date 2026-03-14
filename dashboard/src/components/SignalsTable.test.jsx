import { render, screen } from '@testing-library/react';
import SignalsTable from './SignalsTable';

const mockSignals = [
  {
    symbol: 'AAPL',
    timestamp: '2026-03-13T20:42:00+00:00',
    recommendation: 'hold',
    confidence: 0.3,
    model_id: 'ma_crossover_v1',
    metadata: {},
  },
  {
    symbol: 'MSFT',
    timestamp: '2026-03-13T21:00:00+00:00',
    recommendation: 'buy',
    confidence: 0.85,
    model_id: 'rsi_v2',
    metadata: {},
  },
];

describe('SignalsTable', () => {
  it('renders table headers when signals are provided', () => {
    render(<SignalsTable signals={mockSignals} />);
    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Timestamp')).toBeInTheDocument();
    expect(screen.getByText('Rec.')).toBeInTheDocument();
    expect(screen.getByText('Conf.')).toBeInTheDocument();
    expect(screen.getByText('Model')).toBeInTheDocument();
  });

  it('renders signal rows with correct data', () => {
    render(<SignalsTable signals={mockSignals} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('ma_crossover_v1')).toBeInTheDocument();
    expect(screen.getByText('rsi_v2')).toBeInTheDocument();
  });

  it('formats confidence as percentage', () => {
    render(<SignalsTable signals={mockSignals} />);
    expect(screen.getByText('30.0%')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('shows empty-state message when signals is null', () => {
    render(<SignalsTable signals={null} />);
    expect(screen.getByText('No signals available')).toBeInTheDocument();
  });

  it('shows empty-state message when signals is undefined', () => {
    render(<SignalsTable signals={undefined} />);
    expect(screen.getByText('No signals available')).toBeInTheDocument();
  });

  it('shows empty-state message when signals is empty array', () => {
    render(<SignalsTable signals={[]} />);
    expect(screen.getByText('No signals available')).toBeInTheDocument();
  });

  it('does not render a table in empty state', () => {
    const { container } = render(<SignalsTable signals={[]} />);
    expect(container.querySelector('table')).not.toBeInTheDocument();
  });
});
