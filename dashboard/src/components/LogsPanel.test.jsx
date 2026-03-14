import { render, screen } from '@testing-library/react';
import LogsPanel from './LogsPanel';

const mockLogs = [
  {
    timestamp: '2026-03-14T03:35:07.651658',
    severity: 'INFO',
    component: 'CalgoSystem',
    message: 'Trading loop started',
  },
  {
    timestamp: '2026-03-14T03:36:00.000000',
    severity: 'WARNING',
    component: 'RiskManager',
    message: 'Position size near limit',
  },
  {
    timestamp: '2026-03-14T03:37:00.000000',
    severity: 'ERROR',
    component: 'TradeExecutor',
    message: 'Order rejected by broker',
  },
];

describe('LogsPanel', () => {
  it('renders log entries', () => {
    render(<LogsPanel logs={mockLogs} />);
    expect(screen.getByText('Trading loop started')).toBeInTheDocument();
    expect(screen.getByText('Position size near limit')).toBeInTheDocument();
    expect(screen.getByText('Order rejected by broker')).toBeInTheDocument();
  });

  it('applies log-info class to INFO rows', () => {
    const { container } = render(<LogsPanel logs={mockLogs} />);
    const infoRow = container.querySelector('.log-info');
    expect(infoRow).toBeInTheDocument();
  });

  it('applies log-warning class to WARNING rows', () => {
    const { container } = render(<LogsPanel logs={mockLogs} />);
    const warningRow = container.querySelector('.log-warning');
    expect(warningRow).toBeInTheDocument();
  });

  it('applies log-error class to ERROR rows', () => {
    const { container } = render(<LogsPanel logs={mockLogs} />);
    const errorRow = container.querySelector('.log-error');
    expect(errorRow).toBeInTheDocument();
  });

  it('INFO and WARNING rows have distinct classes', () => {
    const { container } = render(<LogsPanel logs={mockLogs} />);
    const infoRow = container.querySelector('.log-info');
    const warningRow = container.querySelector('.log-warning');
    expect(infoRow).not.toBe(warningRow);
  });

  it('shows empty-state message when logs is null', () => {
    render(<LogsPanel logs={null} />);
    expect(screen.getByText('No logs available')).toBeInTheDocument();
  });

  it('shows empty-state message when logs is undefined', () => {
    render(<LogsPanel logs={undefined} />);
    expect(screen.getByText('No logs available')).toBeInTheDocument();
  });

  it('shows empty-state message when logs is empty array', () => {
    render(<LogsPanel logs={[]} />);
    expect(screen.getByText('No logs available')).toBeInTheDocument();
  });

  it('renders timestamp, severity, component, and message for each entry', () => {
    render(<LogsPanel logs={[mockLogs[0]]} />);
    expect(screen.getByText('2026-03-14T03:35:07.651658')).toBeInTheDocument();
    expect(screen.getByText('[INFO]')).toBeInTheDocument();
    expect(screen.getByText('CalgoSystem')).toBeInTheDocument();
    expect(screen.getByText('Trading loop started')).toBeInTheDocument();
  });
});
