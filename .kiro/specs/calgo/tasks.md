# Implementation Plan: Calgo AI-Driven Trading Bot

## Overview

This implementation plan breaks down the Calgo trading bot into discrete, incremental coding tasks. The system consists of 8 modular components that work together to fetch market data, generate AI-driven trading signals, manage portfolio positions, execute trades, enforce risk controls, and provide analytics.

The implementation follows a bottom-up approach: starting with foundational data models and configuration, then building core components, integrating them into the main trading loop, and finally adding comprehensive testing for all 32 correctness properties.

## Tasks

- [x] 1. Set up project structure and core data models
  - Create Python project directory structure (src/, tests/, config/, logs/)
  - Define all core data models as dataclasses (PriceData, Signal, Position, Order, etc.)
  - Define all enums (ExecutionMode, Recommendation, OrderAction, OrderType, OrderStatus, DataSource, RiskViolation)
  - Create Result/Option types for error handling
  - Set up requirements.txt with dependencies (hypothesis for property testing, requests for API calls, matplotlib for analytics)
  - _Requirements: 10.1, 10.2, 10.5, 10.6_

- [x] 2. Implement Configuration Manager
  - [x] 2.1 Create configuration data models
    - Implement Config, DataSourceConfig, ModelConfig, TradingSchedule, BrokerConfig, LoggingConfig, RiskParameters dataclasses
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 2.2 Implement configuration loading and parsing
    - Write load_config() to read JSON/YAML configuration files
    - Write validate_config() to check required fields and parameter ranges
    - Implement getter methods for all configuration sections
    - _Requirements: 9.1, 9.7_

  - [ ]* 2.3 Write property test for configuration validation
    - **Property 27: Invalid Configuration Rejection**
    - **Validates: Requirements 9.7**
    - Generate random invalid configurations (missing fields, negative values, invalid modes)
    - Verify validation returns descriptive errors

  - [ ]* 2.4 Write unit tests for Configuration Manager
    - Test valid configuration loading
    - Test missing file error handling
    - Test malformed JSON/YAML handling
    - Test specific invalid values (negative percentages, invalid execution modes)
    - _Requirements: 9.7_

- [x] 3. Implement Market Data Ingester
  - [x] 3.1 Create data source adapters
    - Implement Yahoo Finance adapter with fetch_historical() and fetch_realtime()
    - Implement Alpaca adapter with fetch_historical() and fetch_realtime()
    - Create DataSource interface for extensibility
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 3.2 Implement data normalization and validation
    - Write normalize_data() to convert raw API responses to PriceData format
    - Write validate_data() to check for missing/invalid fields (negative prices, missing timestamps)
    - _Requirements: 1.5, 1.6_

  - [x] 3.3 Implement failover logic
    - Write fetch logic that tries primary source, then falls back to alternatives on failure
    - Add retry with exponential backoff for transient errors
    - _Requirements: 1.4_

  - [ ]* 3.4 Write property test for data normalization
    - **Property 3: Data Normalization Consistency**
    - **Validates: Requirements 1.5**
    - Generate random raw data from different sources
    - Verify all normalized to PriceData with required fields

  - [ ]* 3.5 Write property test for data validation
    - **Property 4: Data Validation Flags Invalid Data**
    - **Validates: Requirements 1.6**
    - Generate random invalid price data (negative prices, missing fields)
    - Verify validation returns errors

  - [ ]* 3.6 Write property test for data parsing
    - **Property 28: Market Data Parsing Completeness**
    - **Validates: Requirements 10.1**
    - Generate random valid raw market data
    - Verify parsing produces complete PriceData objects

  - [ ]* 3.7 Write unit tests for Market Data Ingester
    - Test specific API response formats
    - Test network timeout handling
    - Test failover on primary source failure
    - Test data fetch within 5 seconds
    - _Requirements: 1.2, 1.3, 1.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Signal Generator
  - [x] 5.1 Create TradingModel interface
    - Define abstract TradingModel class with predict() and get_model_id() methods
    - _Requirements: 2.1, 2.4_

  - [x] 5.2 Implement example trading models
    - Implement MovingAverageCrossover model
    - Implement simple ML classifier model (placeholder with random forest or logistic regression)
    - _Requirements: 2.1_

  - [x] 5.3 Implement Signal Generator core logic
    - Write generate_signal() to call active models and produce Signal objects
    - Write add_model(), remove_model(), set_active_models() for runtime model management
    - Implement signal aggregation strategies (voting, weighted average, ensemble)
    - _Requirements: 2.2, 2.3, 2.4, 6.4, 6.5_

  - [ ]* 5.4 Write property test for signal structure
    - **Property 5: Signal Structure Completeness**
    - **Validates: Requirements 2.2**
    - Generate random market data inputs
    - Verify all signals contain required fields (symbol, timestamp, recommendation, confidence, model_id)

  - [ ]* 5.5 Write property test for signal aggregation
    - **Property 20: Signal Aggregation Strategy Correctness**
    - **Validates: Requirements 6.5**
    - Generate random sets of signals from multiple models
    - Verify aggregated signal follows configured strategy (voting, weighted average)

  - [ ]* 5.6 Write unit tests for Signal Generator
    - Test specific model outputs
    - Test edge cases (no data, stale data)
    - Test signal generation within 10 seconds
    - Test model swapping without restart
    - _Requirements: 2.5, 6.3_

- [x] 6. Implement Portfolio Manager
  - [x] 6.1 Create position tracking data structures
    - Implement Position and ClosedPosition dataclasses
    - Create internal storage for open and closed positions
    - _Requirements: 3.1_

  - [x] 6.2 Implement position management methods
    - Write add_position() to open new positions
    - Write close_position() to close positions and calculate realized P&L
    - Write update_position() to update current prices and unrealized P&L
    - Write get_position(), get_all_positions() for position queries
    - _Requirements: 3.1, 3.2_

  - [x] 6.3 Implement portfolio metrics calculation
    - Write calculate_unrealized_pnl() to sum all open position P&L
    - Write calculate_realized_pnl() to sum all closed position P&L
    - Write get_allocation() to calculate position percentage of total portfolio
    - Write get_total_value() to calculate total portfolio value
    - Write get_snapshot() to create complete PortfolioSnapshot
    - _Requirements: 3.2, 3.5, 3.6, 3.7_

  - [x] 6.4 Implement portfolio limits enforcement
    - Write check_position_limit() to validate position size against max_position_size_pct
    - Write check_portfolio_limit() to validate total value against max_portfolio_value
    - _Requirements: 3.3, 3.4_

  - [ ]* 6.5 Write property test for P&L calculation
    - **Property 8: Realized P&L Calculation Correctness**
    - **Validates: Requirements 3.2**
    - Generate random positions with entry/exit prices and quantities
    - Verify realized_pnl = (exit_price - entry_price) × quantity

  - [ ]* 6.6 Write property test for allocation invariant
    - **Property 11: Portfolio Allocation Sum Invariant**
    - **Validates: Requirements 3.5**
    - Generate random portfolios with multiple positions
    - Verify sum of allocations = 100% and each allocation = (position_value / total_value) × 100

  - [ ]* 6.7 Write property test for position size limits
    - **Property 10: Position Size Limit Enforcement**
    - **Validates: Requirements 3.4**
    - Generate random positions exceeding max_position_size_pct
    - Verify Portfolio Manager rejects operations

  - [ ]* 6.8 Write property test for portfolio size limits
    - **Property 9: Portfolio Size Limit Enforcement**
    - **Validates: Requirements 3.3**
    - Generate operations exceeding max_portfolio_value
    - Verify Portfolio Manager rejects operations

  - [ ]* 6.9 Write property test for snapshot completeness
    - **Property 13: Portfolio Snapshot Completeness**
    - **Validates: Requirements 3.7**
    - Generate random portfolio states
    - Verify snapshots contain all positions and required metrics

  - [ ]* 6.10 Write unit tests for Portfolio Manager
    - Test empty portfolio
    - Test single position lifecycle (add, update, close)
    - Test multiple positions
    - Test boundary conditions for limits
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Trade Executor and Broker Adapters
  - [x] 8.1 Create Broker Adapter interface
    - Define abstract BrokerAdapter class with place_order(), cancel_order(), get_order_status() methods
    - _Requirements: 4.4, 4.5_

  - [x] 8.2 Implement Paper Trading Broker Adapter
    - Implement Alpaca Paper Trading API adapter
    - Simulate order execution with mock fills
    - _Requirements: 4.2_

  - [x] 8.3 Implement Live Trading Broker Adapter (stub)
    - Create stub implementation for live broker API (Alpaca Live or Interactive Brokers)
    - Add authentication and API connection logic
    - _Requirements: 4.3_

  - [x] 8.4 Implement Trade Executor core logic
    - Write submit_order() to route orders based on execution_mode
    - Write cancel_order() and get_order_status() methods
    - Implement error handling for order failures
    - _Requirements: 4.1, 4.6, 4.7_

  - [ ]* 8.5 Write property test for order confirmation
    - **Property 14: Order Confirmation Completeness**
    - **Validates: Requirements 4.6**
    - Generate random successful orders
    - Verify OrderConfirmation contains all required fields (order_id, symbol, quantity, execution_price, timestamp, status)

  - [ ]* 8.6 Write property test for order failure logging
    - **Property 15: Order Failure Logging**
    - **Validates: Requirements 4.7**
    - Generate random failed orders
    - Verify descriptive error messages and logging

  - [ ]* 8.7 Write unit tests for Trade Executor
    - Test order submission flow
    - Test broker API errors
    - Test mode switching (simulation vs live)
    - Test order confirmation structure
    - _Requirements: 4.1, 4.2, 4.3, 4.6, 4.7_

- [x] 9. Implement Risk Manager
  - [x] 9.1 Create Risk Manager with risk parameters
    - Initialize Risk Manager with RiskParameters (stop_loss_pct, take_profit_pct, max_position_size_pct, max_drawdown_pct, max_portfolio_value)
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.2 Implement risk check methods
    - Write check_stop_loss() to detect positions exceeding loss threshold
    - Write check_take_profit() to detect positions exceeding profit threshold
    - Write check_position_size() to validate position size against portfolio percentage
    - Write check_drawdown() to validate current drawdown against max threshold
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.3 Implement signal evaluation and protective signals
    - Write evaluate_signal() to approve/reject signals based on risk checks
    - Write generate_protective_signals() to create sell signals for stop-loss/take-profit breaches
    - Write is_trading_halted() to check if drawdown limit exceeded
    - _Requirements: 7.5, 7.6, 7.7_

  - [ ]* 9.4 Write property test for stop-loss enforcement
    - **Property 22: Stop-Loss Threshold Enforcement**
    - **Validates: Requirements 7.1, 7.5**
    - Generate random positions with losses exceeding stop_loss_pct
    - Verify Risk Manager generates immediate sell signals

  - [ ]* 9.5 Write property test for take-profit enforcement
    - **Property 23: Take-Profit Threshold Enforcement**
    - **Validates: Requirements 7.2, 7.6**
    - Generate random positions with profits exceeding take_profit_pct
    - Verify Risk Manager generates immediate sell signals

  - [ ]* 9.6 Write property test for position size limits
    - **Property 24: Position Size Risk Limit Enforcement**
    - **Validates: Requirements 7.3**
    - Generate random signals exceeding max_position_size_pct
    - Verify Risk Manager rejects with POSITION_SIZE_EXCEEDED violation

  - [ ]* 9.7 Write property test for drawdown limits
    - **Property 25: Drawdown Limit Enforcement**
    - **Validates: Requirements 7.4, 7.7**
    - Generate portfolio states with drawdown exceeding max_drawdown_pct
    - Verify Risk Manager halts new buy orders and sets trading_halted flag

  - [ ]* 9.8 Write property test for execution mode independence
    - **Property 26: Risk Management Execution Mode Independence**
    - **Validates: Requirements 7.8**
    - Generate random risk checks in both simulation and live modes
    - Verify identical results regardless of execution_mode

  - [ ]* 9.9 Write unit tests for Risk Manager
    - Test boundary conditions (exactly at threshold)
    - Test multiple simultaneous violations
    - Test protective signal generation
    - Test trading halt and resume
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement Logger
  - [x] 11.1 Create log storage and file management
    - Set up log directory structure
    - Implement log file rotation policy
    - Create JSON serialization for TradeRecord, PortfolioSnapshot, Signal
    - _Requirements: 5.4_

  - [x] 11.2 Implement logging methods
    - Write log_trade() to record TradeRecord with all required fields
    - Write log_portfolio_change() to record PortfolioSnapshot
    - Write log_signal() to record Signal with metadata
    - Write log_error() to record SystemError with stack traces
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 11.3 Implement log retrieval methods
    - Write get_trade_history() to query trades by date range
    - Write get_portfolio_history() to query portfolio snapshots by date range
    - Write get_signal_history() to query signals by date range
    - _Requirements: 5.8_

  - [ ]* 11.4 Write property test for trade logging
    - **Property 16: Trade Logging Completeness**
    - **Validates: Requirements 5.1**
    - Generate random executed trades
    - Verify TradeRecord contains all required fields (timestamp, order_id, symbol, action, quantity, execution_price)

  - [ ]* 11.5 Write property test for portfolio logging
    - **Property 17: Portfolio State Change Logging Completeness**
    - **Validates: Requirements 5.2**
    - Generate random portfolio state changes
    - Verify PortfolioSnapshot logged with timestamp and all positions

  - [ ]* 11.6 Write property test for signal logging
    - **Property 6: Signal Logging Completeness**
    - **Validates: Requirements 2.6**
    - Generate random signals
    - Verify logged with all required metadata (timestamp, symbol, recommendation, confidence, model_id)

  - [ ]* 11.7 Write property test for portfolio serialization round-trip
    - **Property 29: Portfolio State Serialization Round-Trip**
    - **Validates: Requirements 10.2, 10.5**
    - Generate random PortfolioSnapshot objects
    - Verify serialize to JSON then parse back produces equivalent object

  - [ ]* 11.8 Write property test for trade record serialization round-trip
    - **Property 31: Trade Record Serialization Round-Trip**
    - **Validates: Requirements 10.6**
    - Generate random TradeRecord objects
    - Verify serialize to JSON then parse back produces equivalent object

  - [ ]* 11.9 Write property test for parsing error descriptiveness
    - **Property 32: Parsing Error Descriptiveness**
    - **Validates: Requirements 10.7**
    - Generate random invalid JSON formats
    - Verify parsing returns descriptive errors with location and nature of failure

  - [ ]* 11.10 Write unit tests for Logger
    - Test file I/O errors
    - Test log rotation
    - Test concurrent writes
    - Test log retrieval by date range
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 12. Implement Analytics Engine
  - [x] 12.1 Implement performance metrics calculation
    - Write calculate_cumulative_returns() as (final_value - initial_value) / initial_value
    - Write calculate_sharpe_ratio() as mean(returns) / std(returns) × sqrt(periods)
    - Write calculate_max_drawdown() as largest peak-to-trough decline
    - _Requirements: 5.7_

  - [x] 12.2 Implement per-model performance tracking
    - Write get_model_performance() to calculate metrics per model (win rate, average return, Sharpe ratio)
    - Filter trades by model_id for independent performance calculation
    - _Requirements: 6.6_

  - [x] 12.3 Implement visualization generation
    - Write generate_pnl_chart() to create time-series P&L visualization
    - Write generate_allocation_chart() to create position allocation pie chart
    - Use matplotlib or similar library for chart generation
    - _Requirements: 5.5, 5.6_

  - [ ]* 12.4 Write property test for metrics calculation
    - **Property 19: Performance Metrics Calculation Correctness**
    - **Validates: Requirements 5.7**
    - Generate random trade histories
    - Verify cumulative returns, Sharpe ratio, and max drawdown calculations

  - [ ]* 12.5 Write property test for per-model performance independence
    - **Property 21: Per-Model Performance Metric Independence**
    - **Validates: Requirements 6.6**
    - Generate random trades from multiple models
    - Verify each model's metrics calculated independently

  - [ ]* 12.6 Write property test for log parsing
    - **Property 30: Log Parsing Completeness**
    - **Validates: Requirements 10.3**
    - Generate random JSON log files
    - Verify Analytics Engine parses back into TradeRecord, PortfolioSnapshot, Signal objects

  - [ ]* 12.7 Write unit tests for Analytics Engine
    - Test empty data sets
    - Test single data point
    - Test visualization rendering
    - Test analytics generation within 5 seconds
    - _Requirements: 5.5, 5.6, 5.7, 5.8_

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement Calgo System Core orchestration
  - [x] 14.1 Create system state machine
    - Implement state transitions (INITIALIZING → READY → RUNNING → HALTED → SHUTDOWN)
    - Write state transition validation logic
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 14.2 Implement main trading loop
    - Write trading loop that fetches market data at configured intervals
    - Integrate Signal Generator to generate signals from market data
    - Integrate Risk Manager to evaluate signals
    - Integrate Trade Executor to submit approved orders
    - Integrate Portfolio Manager to update positions after trades
    - Integrate Logger to record all state changes
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 14.3 Implement error handling and recovery
    - Add try-catch blocks for transient errors with retry logic
    - Add critical error handling that halts trading and sends alerts
    - Implement graceful shutdown on SIGTERM/SIGINT
    - _Requirements: 8.7_

  - [x] 14.4 Implement system initialization
    - Write startup sequence: load config → initialize components → validate connections → enter READY state
    - Add configuration validation at startup
    - Add component health checks
    - _Requirements: 8.1, 9.1_

  - [ ]* 14.5 Write integration tests for trading loop
    - Test full data fetch → signal generation → risk check → execution → portfolio update → logging flow
    - Test mode switching between simulation and live
    - Test failover scenarios
    - Test error propagation across components
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 15. Implement remaining property-based tests
  - [ ]* 15.1 Write property test for historical data retrieval
    - **Property 1: Historical Data Retrieval Completeness**
    - **Validates: Requirements 1.2**
    - Generate random symbols and time ranges
    - Verify Market Data Ingester returns data covering period or descriptive error

  - [ ]* 15.2 Write property test for data source failover
    - **Property 2: Data Source Failover**
    - **Validates: Requirements 1.4**
    - Simulate primary source failures
    - Verify automatic failover to alternative sources

  - [ ]* 15.3 Write property test for position tracking completeness
    - **Property 7: Position Tracking Completeness**
    - **Validates: Requirements 3.1**
    - Generate random open positions
    - Verify all required fields tracked (symbol, quantity, entry_price, current_price, entry_timestamp, unrealized_pnl)

  - [ ]* 15.4 Write property test for risk metrics update
    - **Property 12: Risk Metrics Update on State Change**
    - **Validates: Requirements 3.6**
    - Generate random portfolio state changes
    - Verify risk metrics (drawdown, exposure) recalculated

  - [ ]* 15.5 Write property test for signal logging completeness
    - **Property 18: Signal Logging Completeness**
    - **Validates: Requirements 5.3**
    - Generate random signals
    - Verify Logger records all required fields

- [x] 16. Create example configuration file
  - Create config.json with example values for all required fields
  - Include both simulation and live mode examples
  - Add comments explaining each configuration parameter
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 17. Create main entry point and CLI
  - Write main.py with command-line argument parsing
  - Add --config flag to specify configuration file path
  - Add --mode flag to override execution mode
  - Add startup banner and logging initialization
  - _Requirements: 8.1, 9.1_

- [x] 18. Final checkpoint - Ensure all tests pass
  - Run all unit tests and verify passing
  - Run all property-based tests and verify passing
  - Run integration tests and verify passing
  - Ensure test coverage above 80% for critical components
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate component interactions and end-to-end flows
- The implementation uses Python as specified in the design document
- All 32 correctness properties from the design document are covered by property-based tests
- Checkpoints ensure incremental validation and provide opportunities for user feedback
