# Requirements Document

## Introduction

The Trading Dashboard is a real-time observability layer for the calgo autonomous trading bot. It consists of two components: a FastAPI backend (`dashboard_api.py`) that reads calgo's on-disk data files and exposes them as REST endpoints, and a React frontend (`dashboard/`) that polls those endpoints and renders price history charts, trading signals, executed trades, portfolio snapshots, and system logs. The goal is to let a developer run the bot and the dashboard side by side and see what the bot is doing in near real time.

## Glossary

- **API_Server**: The FastAPI application (`dashboard_api.py`) that serves calgo data over HTTP.
- **Dashboard**: The React single-page application in the `dashboard/` directory.
- **Price_History**: OHLCV records stored in `cache/historical/{SYMBOL}.json`.
- **Signal**: A trading recommendation entry stored in `logs/signals/{date}.json`, containing symbol, timestamp, recommendation, confidence, model_id, and metadata.
- **Trade**: An executed trade entry stored in `logs/trades/{date}.json`.
- **Portfolio_Snapshot**: A portfolio state entry stored in `logs/portfolio/{date}.json`.
- **Log_Entry**: A system/error log entry stored in `logs/errors/{date}.json`, containing timestamp, severity, component, and message.
- **Symbol**: A stock ticker string (e.g. `AAPL`, `MSFT`, `GOOGL`).
- **Polling_Interval**: The configurable period in seconds at which the Dashboard re-fetches data from the API_Server.

---

## Requirements

### Requirement 1: Serve Historical Price Data

**User Story:** As a developer monitoring the bot, I want to retrieve historical OHLCV price data for any tracked symbol, so that I can visualize price history in the dashboard.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/price-history/{symbol}`, THE API_Server SHALL return the full contents of `cache/historical/{symbol}.json` as a JSON response.
2. IF the requested symbol's cache file does not exist, THEN THE API_Server SHALL return an HTTP 404 response with a descriptive error message.
3. IF the cache file exists but cannot be parsed as valid JSON, THEN THE API_Server SHALL return an HTTP 500 response with a descriptive error message.
4. THE API_Server SHALL return symbol names in uppercase regardless of the case used in the request path.

---

### Requirement 2: Serve Trading Signals

**User Story:** As a developer monitoring the bot, I want to retrieve trading signals for a given date, so that I can see what recommendations the bot generated.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/signals/{date}`, THE API_Server SHALL return all Signal entries from `logs/signals/{date}.json` as a JSON array.
2. WHEN a GET request is made to `/api/signals` with no date parameter, THE API_Server SHALL return Signal entries from today's log file.
3. IF the signals log file for the requested date does not exist, THEN THE API_Server SHALL return an empty JSON array.
4. THE API_Server SHALL return Signal entries sorted by timestamp in ascending order.

---

### Requirement 3: Serve Executed Trades

**User Story:** As a developer monitoring the bot, I want to retrieve executed trades for a given date, so that I can audit what the bot actually did.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/trades/{date}`, THE API_Server SHALL return all Trade entries from `logs/trades/{date}.json` as a JSON array.
2. WHEN a GET request is made to `/api/trades` with no date parameter, THE API_Server SHALL return Trade entries from today's log file.
3. IF the trades log file for the requested date does not exist, THEN THE API_Server SHALL return an empty JSON array.
4. THE API_Server SHALL return Trade entries sorted by timestamp in ascending order.

---

### Requirement 4: Serve Portfolio Snapshots

**User Story:** As a developer monitoring the bot, I want to retrieve portfolio snapshots for a given date, so that I can track how the portfolio value and positions changed over time.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/portfolio/{date}`, THE API_Server SHALL return all Portfolio_Snapshot entries from `logs/portfolio/{date}.json` as a JSON array.
2. WHEN a GET request is made to `/api/portfolio` with no date parameter, THE API_Server SHALL return Portfolio_Snapshot entries from today's log file.
3. IF the portfolio log file for the requested date does not exist, THEN THE API_Server SHALL return an empty JSON array.
4. THE API_Server SHALL return Portfolio_Snapshot entries sorted by timestamp in ascending order.

---

### Requirement 5: Serve System Logs

**User Story:** As a developer monitoring the bot, I want to retrieve system and error log entries for a given date, so that I can diagnose issues and observe bot lifecycle events.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/logs/{date}`, THE API_Server SHALL return all Log_Entry records from `logs/errors/{date}.json` as a JSON array.
2. WHEN a GET request is made to `/api/logs` with no date parameter, THE API_Server SHALL return Log_Entry records from today's log file.
3. IF the log file for the requested date does not exist, THEN THE API_Server SHALL return an empty JSON array.
4. WHERE a `severity` query parameter is provided, THE API_Server SHALL filter Log_Entry records to only those matching the specified severity value.
5. THE API_Server SHALL return Log_Entry records sorted by timestamp in ascending order.

---

### Requirement 6: List Available Symbols

**User Story:** As a developer, I want to discover which symbols have cached price data, so that the dashboard can populate its symbol selector automatically.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/symbols`, THE API_Server SHALL return a JSON array of Symbol strings for which a cache file exists in `cache/historical/`.
2. THE API_Server SHALL return Symbol strings in uppercase.
3. IF no cache files exist, THE API_Server SHALL return an empty JSON array.

---

### Requirement 7: List Available Log Dates

**User Story:** As a developer, I want to know which dates have log data available, so that I can navigate to historical sessions in the dashboard.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/dates`, THE API_Server SHALL return a JSON object containing arrays of available dates for each log type (`signals`, `trades`, `portfolio`, `errors`).
2. THE API_Server SHALL derive dates from the filenames in the respective `logs/` subdirectories using the `{date}.json` naming convention.
3. THE API_Server SHALL return dates as strings in `YYYY-MM-DD` format, sorted in descending order (most recent first).

---

### Requirement 8: Cross-Origin Resource Sharing

**User Story:** As a developer running the React frontend on a different port than the API, I want the API to allow cross-origin requests, so that the browser does not block dashboard requests.

#### Acceptance Criteria

1. THE API_Server SHALL include CORS headers that permit requests from any origin during development.
2. THE API_Server SHALL allow the HTTP methods GET, OPTIONS.

---

### Requirement 9: Display Price History Chart

**User Story:** As a developer monitoring the bot, I want to see a candlestick or line chart of historical price data for a selected symbol, so that I can understand the market context for bot decisions.

#### Acceptance Criteria

1. THE Dashboard SHALL display a price history chart for the currently selected Symbol.
2. WHEN the user selects a different Symbol from the symbol selector, THE Dashboard SHALL fetch and render the price history for the newly selected Symbol.
3. THE Dashboard SHALL render at minimum the closing price over time as a line chart.
4. IF no price data is available for the selected Symbol, THE Dashboard SHALL display a descriptive empty-state message.

---

### Requirement 10: Display Trading Signals

**User Story:** As a developer monitoring the bot, I want to see the latest trading signals in the dashboard, so that I can understand what the bot is recommending.

#### Acceptance Criteria

1. THE Dashboard SHALL display a list or table of Signal entries for the currently viewed date.
2. THE Dashboard SHALL show at minimum the symbol, timestamp, recommendation, confidence, and model_id for each Signal.
3. WHEN the Dashboard polls and new Signal entries are available, THE Dashboard SHALL update the signals view without requiring a page reload.

---

### Requirement 11: Display Executed Trades

**User Story:** As a developer monitoring the bot, I want to see executed trades in the dashboard, so that I can verify the bot is acting on its signals.

#### Acceptance Criteria

1. THE Dashboard SHALL display a list or table of Trade entries for the currently viewed date.
2. WHEN the Dashboard polls and new Trade entries are available, THE Dashboard SHALL update the trades view without requiring a page reload.

---

### Requirement 12: Display Portfolio State

**User Story:** As a developer monitoring the bot, I want to see the current portfolio snapshot in the dashboard, so that I can track positions and overall value.

#### Acceptance Criteria

1. THE Dashboard SHALL display the most recent Portfolio_Snapshot for the currently viewed date.
2. WHEN the Dashboard polls and a newer Portfolio_Snapshot is available, THE Dashboard SHALL update the portfolio view without requiring a page reload.

---

### Requirement 13: Display System Logs

**User Story:** As a developer monitoring the bot, I want to see system log entries in the dashboard, so that I can observe bot lifecycle events and diagnose errors.

#### Acceptance Criteria

1. THE Dashboard SHALL display a scrollable list of Log_Entry records for the currently viewed date.
2. THE Dashboard SHALL visually distinguish log entries by severity (e.g. INFO, WARNING, ERROR).
3. WHEN the Dashboard polls and new Log_Entry records are available, THE Dashboard SHALL append them to the log view without requiring a page reload.

---

### Requirement 14: Near Real-Time Polling

**User Story:** As a developer running the bot and dashboard side by side, I want the dashboard to automatically refresh its data, so that I can observe bot activity without manually reloading.

#### Acceptance Criteria

1. THE Dashboard SHALL poll all active data endpoints at a configurable Polling_Interval.
2. THE Dashboard SHALL use a default Polling_Interval of 10 seconds.
3. WHILE the Dashboard is polling, THE Dashboard SHALL not block user interaction or cause visible page flicker.
4. IF a poll request fails, THEN THE Dashboard SHALL display a non-blocking error indicator and continue polling on the next interval.

---

### Requirement 15: API Health Check

**User Story:** As a developer, I want a health check endpoint so that I can verify the API server is running before starting the dashboard.

#### Acceptance Criteria

1. WHEN a GET request is made to `/api/health`, THE API_Server SHALL return an HTTP 200 response with a JSON body indicating the server is healthy.
2. THE API_Server SHALL include the current server timestamp in the health check response.
