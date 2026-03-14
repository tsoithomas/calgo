# Implementation Plan: Trading Dashboard

## Overview

Implement a FastAPI backend (`dashboard_api.py`) and a React/Vite frontend (`dashboard/`) that provide near real-time observability into the calgo trading bot. The backend reads on-disk data files and exposes REST endpoints; the frontend polls those endpoints every 10 seconds and renders charts, tables, and logs.

## Tasks

- [x] 1. Create the FastAPI API server (`dashboard_api.py`)
  - [x] 1.1 Scaffold `dashboard_api.py` at the project root with FastAPI, CORS middleware (all origins), and the `/api/health` endpoint returning `{"status": "ok", "timestamp": <ISO8601>}`
    - _Requirements: 8.1, 8.2, 15.1, 15.2_
  - [x] 1.2 Write property test for health endpoint timestamp (Property 6)
    - **Property 6: Health response contains timestamp**
    - **Validates: Requirements 15.2**
    - Use Hypothesis to call `/api/health` repeatedly and assert `timestamp` is always present and parseable as ISO 8601
    - Tag: `# Feature: trading-dashboard, Property 6: Health response contains timestamp`

- [x] 2. Implement file-reading helpers and `/api/symbols` + `/api/dates`
  - [x] 2.1 Implement `read_json_file(path)`, `list_dated_files(log_dir)`, and `sort_by_timestamp(entries)` helpers inside `dashboard_api.py`
    - `read_json_file` returns `None` on missing file, raises on corrupt JSON
    - `list_dated_files` returns sorted date strings from `{date}.json` filenames
    - `sort_by_timestamp` sorts dicts by `"timestamp"` ascending
    - _Requirements: 2.4, 3.4, 4.4, 5.5_
  - [x] 2.2 Implement `GET /api/symbols` — scan `cache/historical/`, return uppercase symbol names as a JSON array
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 2.3 Implement `GET /api/dates` — return descending-sorted date arrays for `signals`, `trades`, `portfolio`, `errors`
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 2.4 Write property test for dates derived from filenames (Property 5)
    - **Property 5: Dates derived from filenames**
    - **Validates: Requirements 7.2, 7.3**
    - Generate random sets of `YYYY-MM-DD` strings, create temp `.json` files, assert `/api/dates` returns exactly those dates in descending order
    - Tag: `# Feature: trading-dashboard, Property 5: Dates derived from filenames`
  - [x] 2.5 Write unit tests for helpers and symbol/dates endpoints
    - Test `GET /api/symbols` returns uppercase; test `GET /api/dates` descending order; test empty `cache/` returns `[]`
    - Use `pytest` + `TestClient` + `tmp_path`
    - _Requirements: 6.1, 6.2, 6.3, 7.1, 7.2, 7.3_

- [x] 3. Implement `/api/price-history/{symbol}`
  - [x] 3.1 Implement `GET /api/price-history/{symbol}` — uppercase the symbol, read `cache/historical/{SYMBOL}.json`, return full JSON; 404 if missing, 500 if corrupt
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 3.2 Write property test for symbol case normalization (Property 1)
    - **Property 1: Symbol case normalization**
    - **Validates: Requirements 1.4, 6.2**
    - Generate random mixed-case symbol strings, assert response symbol field is uppercase
    - Tag: `# Feature: trading-dashboard, Property 1: Symbol case normalization`
  - [x] 3.3 Write unit tests for price-history endpoint
    - Test lowercase request returns uppercase symbol; test unknown symbol returns 404; test corrupt file returns 500
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 4. Implement log endpoints (`/api/signals`, `/api/trades`, `/api/portfolio`, `/api/logs`)
  - [x] 4.1 Implement `GET /api/signals[/{date}]` and `GET /api/trades[/{date}]` — read respective log files, return timestamp-sorted arrays; return `[]` if file missing or corrupt
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_
  - [x] 4.2 Implement `GET /api/portfolio[/{date}]` and `GET /api/logs[/{date}]` — same pattern; `/api/logs` additionally supports `?severity=` query param filtering
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_
  - [x] 4.3 Write property test for missing file returns safe default (Property 2)
    - **Property 2: Missing file returns safe default**
    - **Validates: Requirements 2.3, 3.3, 4.3, 5.3**
    - Generate random date strings with no corresponding file; assert all four log endpoints return `[]`
    - Tag: `# Feature: trading-dashboard, Property 2: Missing file returns safe default`
  - [x] 4.4 Write property test for timestamp sort order (Property 3)
    - **Property 3: Timestamp sort order**
    - **Validates: Requirements 2.4, 3.4, 4.4, 5.5**
    - Generate lists of entry dicts with random ISO timestamps, write to temp file, assert API response is sorted ascending
    - Tag: `# Feature: trading-dashboard, Property 3: Timestamp sort order`
  - [x] 4.5 Write property test for severity filter is a subset (Property 4)
    - **Property 4: Severity filter is a subset**
    - **Validates: Requirements 5.4**
    - Generate log entries with random severities from `{INFO, WARNING, ERROR}`; assert filtered response is a subset of unfiltered and all entries match the severity
    - Tag: `# Feature: trading-dashboard, Property 4: Severity filter is a subset`
  - [x] 4.6 Write unit tests for log endpoints
    - Test missing file returns `[]`; test `?severity=WARNING` filters correctly; test corrupt log file returns `[]`
    - _Requirements: 2.3, 3.3, 4.3, 5.3, 5.4_

- [x] 5. Checkpoint — Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Scaffold the React frontend (`dashboard/`)
  - [x] 6.1 Bootstrap a Vite + React project in `dashboard/` with Tailwind CSS and Recharts installed
    - Run: `npm create vite@latest dashboard -- --template react`, then install `tailwindcss`, `recharts`
    - _Requirements: 9.1, 10.1, 11.1, 12.1, 13.1_
  - [x] 6.2 Create `dashboard/src/api.js` — thin `fetch` wrapper with base URL `http://localhost:8000`; export one function per endpoint
    - _Requirements: 9.1, 10.1, 11.1, 12.1, 13.1, 14.1_

- [x] 7. Implement `usePolling` hook and data hooks
  - [x] 7.1 Implement `usePolling(fetchFn, intervalMs)` in `dashboard/src/hooks/usePolling.js` — calls `fetchFn` on mount and every `intervalMs` ms; returns `{ data, error, loading }`; catches errors per-call without stopping the interval
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  - [x] 7.2 Implement `useSymbols`, `useDates`, `usePriceHistory(symbol)`, `useSignals(date)`, `useTrades(date)`, `usePortfolio(date)`, `useLogs(date)` in `dashboard/src/hooks/` — each wraps `usePolling` with the appropriate API call and 10 s default interval
    - _Requirements: 14.1, 14.2_
  - [x] 7.3 Write Vitest tests for `usePolling` hook (Property 7)
    - **Property 7: Polling does not block interaction**
    - **Validates: Requirements 14.4**
    - Assert fetch is called on mount and re-called after interval; assert error state is set on fetch failure without stopping the interval
    - Tag: `# Feature: trading-dashboard, Property 7: Polling does not block interaction`

- [x] 8. Implement UI components
  - [x] 8.1 Implement `Header` component — symbol selector (populated from `useSymbols`), date picker (populated from `useDates`), polling indicator
    - _Requirements: 9.2, 14.3_
  - [x] 8.2 Implement `PriceChart` component — Recharts `LineChart` of close prices from `usePriceHistory`; show empty-state message when no data
    - _Requirements: 9.1, 9.3, 9.4_
  - [x] 8.3 Implement `SignalsTable` and `TradesTable` components — display symbol, timestamp, recommendation, confidence, model_id; show empty-state message when no data
    - _Requirements: 10.1, 10.2, 10.3, 11.1, 11.2_
  - [x] 8.4 Implement `PortfolioPanel` component — display most recent snapshot; show empty-state message when no data
    - _Requirements: 12.1, 12.2_
  - [x] 8.5 Implement `LogsPanel` component — scrollable list with severity-colored rows (INFO/WARNING/ERROR); show empty-state message when no data
    - _Requirements: 13.1, 13.2, 13.3_
  - [x] 8.6 Write Vitest tests for `PriceChart` — given mock price records, assert `<svg>` is rendered; given `[]`, assert empty-state message is rendered
    - _Requirements: 9.3, 9.4_
  - [x] 8.7 Write Vitest tests for `LogsPanel` — given entries of mixed severity, assert INFO/WARNING/ERROR rows have distinct CSS classes
    - _Requirements: 13.2_

- [x] 9. Wire everything together in `App`
  - [x] 9.1 Implement `App` component — compose `Header`, `PriceChart`, `SignalsTable`, `TradesTable`, `PortfolioPanel`, `LogsPanel`; render a dismissible error banner when any hook has a non-null error
    - _Requirements: 14.3, 14.4_
  - [x] 9.2 Write Vitest integration test for `App` error banner — mock a failing fetch, assert non-blocking error banner renders and other panels still render
    - _Requirements: 14.4_

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all backend (`pytest`) and frontend (`vitest --run`) tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Backend property tests use `hypothesis` (already in the project); tag each with the property number comment
- Backend unit tests use `pytest` + `httpx.AsyncClient` / `TestClient` + `tmp_path` fixtures
- Frontend tests use `vitest --run` + React Testing Library
- The API server is read-only and stateless — no writes to calgo data files
- Property tests require minimum 100 iterations each
