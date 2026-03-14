import { render, screen } from '@testing-library/react';
import PortfolioPanel from './PortfolioPanel';

const snapshots = [
  { timestamp: '2026-03-13T10:00:00', total_value: 10000, cash: 5000 },
  { timestamp: '2026-03-13T11:00:00', total_value: 10500, cash: 4500, positions: '{"AAPL": 2}' },
];

describe('PortfolioPanel', () => {
  it('displays the most recent snapshot fields', () => {
    render(<PortfolioPanel snapshots={snapshots} />);
    expect(screen.getByText('10500')).toBeInTheDocument();
    expect(screen.getByText('4500')).toBeInTheDocument();
  });

  it('does not display fields from older snapshots', () => {
    render(<PortfolioPanel snapshots={snapshots} />);
    expect(screen.queryByText('10000')).not.toBeInTheDocument();
  });

  it('shows empty-state when snapshots is null', () => {
    render(<PortfolioPanel snapshots={null} />);
    expect(screen.getByText('No portfolio data available')).toBeInTheDocument();
  });

  it('shows empty-state when snapshots is undefined', () => {
    render(<PortfolioPanel snapshots={undefined} />);
    expect(screen.getByText('No portfolio data available')).toBeInTheDocument();
  });

  it('shows empty-state when snapshots is empty array', () => {
    render(<PortfolioPanel snapshots={[]} />);
    expect(screen.getByText('No portfolio data available')).toBeInTheDocument();
  });

  it('renders field labels with underscores replaced by spaces', () => {
    render(<PortfolioPanel snapshots={snapshots} />);
    expect(screen.getByText('total value')).toBeInTheDocument();
  });
});
