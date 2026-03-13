# Requirements Document

## Introduction

The historical data cache feature enables the Calgo trading bot to persist downloaded market price history to disk and pre-seed trading model state on startup. Currently, the `MovingAverageCrossover` model stores price history only in memory, meaning every restart requires the bot to accumulate `long_window` (50) live data points before generating any signals — at a 5-minute fetch interval, that is over 4 hours of warm-up time. This feature eliminates that delay by caching historical bars to disk and loading them back into model state during initialization.

## Glossary

- **Cache**: A disk-backed store of serialized `PriceData` records, keyed by symbol and date range.
- **Cache_Manager**: The new component responsible for reading and writing the disk cache.
- **MarketDataIngester**: The existing component that fetches price data from Alpaca and Yahoo Finance.
- **MovingAverageCrossover**: The existing trading model that maintains an in-memory `_price_history` dict per symbol.
- **Price_History**: The ordered list of closing prices maintained by a trading model for a given symbol.
- **Seed_Data**: Historical `PriceData` records loaded from the cache or fetched from a data source, used to pre-populate model price history on startup.
- **CalgoSystem**: The main orchestrator that initializes and coordinates all components.
- **long_window**: The number of historical data points required by `MovingAverageCrossover` to compute the long moving average (default: 50).
- **Cache_Entry**: A single cached dataset for one symbol, containing a list of `PriceData` records and metadata (symbol, fetch timestamp, data date range).
- **Stale_Cache**: A cache entry whose most recent data point is older than one trading day relative to the current date.

---

## Requirements

### Requirement 1: Disk Cache Storage

**User Story:** As a bot operator, I want historical price data to be saved to disk, so that the bot does not re-download the same data on every restart.

#### Acceptance Criteria

1. THE Cache_Manager SHALL serialize `PriceData` records to a JSON file on disk, one file per symbol.
2. THE Cache_Manager SHALL store cache files under a configurable directory (default: `./cache/historical`).
3. WHEN the cache directory does not exist, THE Cache_Manager SHALL create it before writing.
4. THE Cache_Manager SHALL include the symbol name, fetch timestamp, and data date range as metadata in each cache file.
5. IF a cache file cannot be written due to a filesystem error, THEN THE Cache_Manager SHALL return a descriptive error and leave any existing cache file unchanged.

---

### Requirement 2: Disk Cache Retrieval

**User Story:** As a bot operator, I want the bot to load previously cached price data from disk, so that startup is fast and does not depend on network availability.

#### Acceptance Criteria

1. WHEN a cache file exists for a symbol, THE Cache_Manager SHALL deserialize it into a list of `PriceData` records.
2. WHEN a cache file does not exist for a symbol, THE Cache_Manager SHALL return an empty result indicating a cache miss.
3. IF a cache file is corrupt or fails to parse, THEN THE Cache_Manager SHALL return a descriptive error and treat the entry as a cache miss.
4. THE Cache_Manager SHALL preserve the original ordering (ascending by timestamp) of `PriceData` records after deserialization.
5. FOR ALL valid `PriceData` lists, serializing then deserializing SHALL produce a list of records equivalent to the original (round-trip property).

---

### Requirement 3: Cache Staleness Detection

**User Story:** As a bot operator, I want stale cached data to be refreshed automatically, so that the model is seeded with recent price history rather than outdated data.

#### Acceptance Criteria

1. WHEN a cache entry is loaded, THE Cache_Manager SHALL compare the most recent data point's date to the current date.
2. WHEN the most recent data point is from a prior trading day or earlier, THE Cache_Manager SHALL mark the entry as stale.
3. WHILE a cache entry is stale, THE CalgoSystem SHALL fetch updated historical data from the MarketDataIngester to replace it.
4. WHEN fresh data is fetched to replace a stale entry, THE Cache_Manager SHALL overwrite the existing cache file with the updated records.
5. IF the staleness check cannot be completed (e.g., empty cache), THEN THE Cache_Manager SHALL treat the entry as stale.

---

### Requirement 4: Startup History Pre-Seeding

**User Story:** As a bot operator, I want the trading model's price history to be populated with historical data on startup, so that the model can generate signals immediately without a warm-up period.

#### Acceptance Criteria

1. WHEN `CalgoSystem.initialize()` completes component setup, THE CalgoSystem SHALL invoke the history pre-seeding process for each configured trading symbol.
2. THE CalgoSystem SHALL load at least `long_window` data points into each `MovingAverageCrossover` model's `_price_history` for each symbol before transitioning to `READY` state.
3. WHEN cached data is available and not stale, THE CalgoSystem SHALL seed the model from the cache without making a network request.
4. WHEN cached data is absent or stale, THE CalgoSystem SHALL fetch historical data via `MarketDataIngester.fetch_historical()` and then seed the model.
5. IF historical data cannot be fetched from any source, THEN THE CalgoSystem SHALL log a warning and transition to `READY` state with whatever data is available, including zero data points.
6. THE CalgoSystem SHALL seed each model with the most recent `long_window` closing prices, ordered ascending by timestamp.

---

### Requirement 5: Historical Fetch Parameters

**User Story:** As a bot operator, I want the system to request an appropriate date range when fetching historical data, so that enough bars are retrieved to satisfy the model's window requirements.

#### Acceptance Criteria

1. WHEN fetching historical data for seeding, THE CalgoSystem SHALL request a date range that covers at least `long_window` trading days prior to the current date.
2. THE CalgoSystem SHALL use a configurable lookback multiplier (default: 2×) applied to `long_window` to account for weekends, holidays, and missing bars.
3. WHEN the fetched dataset contains more than `long_window` records, THE CalgoSystem SHALL use only the most recent `long_window` records for seeding.
4. WHEN the fetched dataset contains fewer than `long_window` records, THE CalgoSystem SHALL use all available records and log the shortfall.

---

### Requirement 6: Cache Configuration

**User Story:** As a bot operator, I want to configure the cache behavior via the existing config file, so that I can adjust cache location and staleness policy without modifying code.

#### Acceptance Criteria

1. THE Cache_Manager SHALL read the cache directory path from a `cache_config.cache_directory` field in `config.json` (default: `./cache/historical`).
2. THE Cache_Manager SHALL read a `cache_config.max_age_days` field from `config.json` that overrides the default staleness threshold (default: 1 day).
3. WHERE `cache_config` is absent from `config.json`, THE Cache_Manager SHALL apply all default values without error.
4. IF a configured cache directory path is invalid or inaccessible, THEN THE Cache_Manager SHALL return a descriptive error during initialization.

---

### Requirement 7: Cache Serialization Format

**User Story:** As a developer, I want the cache file format to be human-readable and easy to inspect, so that I can debug data issues without special tooling.

#### Acceptance Criteria

1. THE Cache_Manager SHALL serialize cache files as UTF-8 encoded JSON.
2. THE Cache_Manager SHALL represent each `PriceData` record as a JSON object with fields: `symbol`, `timestamp` (ISO 8601 string), `open`, `high`, `low`, `close` (all as decimal strings), `volume` (integer), and `source`.
3. THE Cache_Manager SHALL wrap the records array in a top-level JSON object containing `symbol`, `fetched_at` (ISO 8601), `record_count`, and `records` fields.
4. FOR ALL valid cache files, parsing the JSON then re-serializing SHALL produce an equivalent JSON structure (round-trip property).
