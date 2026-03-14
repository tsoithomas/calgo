# Implementation Plan: Historical Data Cache

## Overview

Add a disk-backed JSON cache layer and startup seeding step so `MovingAverageCrossover` models are pre-populated with historical price data before the system transitions to `READY`, eliminating the 4+ hour cold-start warm-up delay.

## Tasks

- [x] 1. Add `CacheConfig` dataclass and wire into `Config`
  - Add `CacheConfig` dataclass to `src/config_models.py` with fields `cache_directory: str = "./cache/historical"` and `max_age_days: int = 1`
  - Add optional `cache_config: CacheConfig` field to the `Config` dataclass with a default instance
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 2. Add `get_cache_config()` to `ConfigurationManager`
  - Add `get_cache_config() -> CacheConfig` method to `src/config_manager.py`
  - Parse the optional `cache_config` section from the config dict in `_parse_config()`; return `CacheConfig()` defaults when the section is absent
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 3. Implement `CacheManager`
  - [x] 3.1 Create `src/cache_manager.py` with `CacheError` exception and `CacheEntry` dataclass (`symbol`, `fetched_at: datetime`, `records: List[PriceData]`)
    - _Requirements: 1.1, 1.4, 2.1_

  - [x] 3.2 Implement `CacheManager.__init__(self, config: CacheConfig)`
    - Validate that the configured directory is accessible (or can be created); return/raise `CacheError` with a descriptive message if not
    - _Requirements: 6.4_

  - [x] 3.3 Implement `CacheManager.write(self, symbol: str, records: List[PriceData]) -> Result[None, CacheError]`
    - Create the cache directory tree if it does not exist (Requirement 1.3)
    - Serialize to UTF-8 JSON with top-level fields `symbol`, `fetched_at` (ISO 8601), `record_count`, and `records`
    - Represent each `PriceData` as a JSON object with `symbol`, `timestamp` (ISO 8601), `open`, `high`, `low`, `close` (decimal strings), `volume` (int), `source`
    - On filesystem error, return `Err(CacheError)` and leave any existing file unchanged (Requirement 1.5)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3_

  - [x] 3.4 Write property test — Property 2: Serialized record field completeness
    - **Property 2: For any `PriceData` record written to a cache file, the JSON object shall contain all required fields with correct types**
    - **Validates: Requirements 7.2**

  - [x] 3.5 Write property test — Property 3: Cache file metadata fields
    - **Property 3: For any non-empty records list, the JSON file shall contain `symbol`, `fetched_at`, `record_count`, and `records` where `record_count == len(records)`**
    - **Validates: Requirements 1.4, 7.3**

  - [x] 3.6 Write property test — Property 4: Cache files written to configured directory
    - **Property 4: After `write()` succeeds, the file shall exist at `{cache_directory}/{SYMBOL}.json`**
    - **Validates: Requirements 1.2, 6.1**

  - [x] 3.7 Implement `CacheManager.read(self, symbol: str) -> Result[CacheEntry | None, CacheError]`
    - Return `Ok(None)` when no cache file exists for the symbol (cache miss)
    - Return `Err(CacheError)` when the file exists but is corrupt or fails to parse
    - Deserialize records preserving ascending timestamp order
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.8 Write property test — Property 1: Serialization round-trip
    - **Property 1: For any valid `List[PriceData]`, `write()` then `read()` shall return an equivalent list in the same order**
    - **Validates: Requirements 2.5, 7.4**

  - [x] 3.9 Implement `CacheManager.is_stale(self, entry: CacheEntry) -> bool`
    - Return `True` when `entry.records` is empty (Requirement 3.5)
    - Return `True` when the most recent record's date is more than `max_age_days` days before today
    - Return `False` when the most recent record's date is within the threshold
    - _Requirements: 3.1, 3.2, 3.5, 6.2_

  - [x] 3.10 Write property test — Property 5: Staleness detection respects `max_age_days`
    - **Property 5: `is_stale()` returns `True` when the most recent record's date is more than `max_age_days` days before today, `False` when within threshold**
    - **Validates: Requirements 3.2, 6.2**

- [x] 4. Checkpoint — Ensure all `CacheManager` tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add cache seeding methods to `CalgoSystem`
  - [x] 5.1 Instantiate `CacheManager` in `CalgoSystem.initialize()` using `get_cache_config()` and store as `self._cache_manager`
    - _Requirements: 4.1_

  - [x] 5.2 Implement `CalgoSystem._fetch_and_cache(self, symbol: str) -> CacheEntry | None`
    - Compute `start_date = today - timedelta(days=long_window * lookback_multiplier)` (default multiplier 2) and `end_date = today`
    - Call `MarketDataIngester.fetch_historical(symbol, start_date, end_date)`
    - On success, call `CacheManager.write()` then return a `CacheEntry`; on failure, log a WARNING and return `None`
    - _Requirements: 3.3, 3.4, 4.4, 4.5, 5.1, 5.2_

  - [x] 5.3 Write property test — Property 9: Lookback date range covers sufficient calendar days
    - **Property 9: For any `long_window` L and multiplier M, `start_date` passed to `fetch_historical()` shall be at least `L * M` calendar days before today**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 5.4 Implement `CalgoSystem._inject_price_history(self, symbol: str, records: List[PriceData]) -> None`
    - Take the most recent `long_window` records (or all if fewer)
    - Write their closing prices (ascending by timestamp) into each `MovingAverageCrossover` model's `_price_history[symbol]`
    - Log a WARNING when `len(records) < long_window`
    - _Requirements: 4.2, 4.6, 5.3, 5.4_

  - [x] 5.5 Write property test — Property 8: Seeding injects the correct closing prices
    - **Property 8: For any dataset of N records and `long_window` L, `_price_history[symbol]` shall contain exactly `min(N, L)` entries equal to the closing prices of the most recent `min(N, L)` records, ascending by timestamp**
    - **Validates: Requirements 4.2, 4.6, 5.3**

  - [x] 5.6 Implement `CalgoSystem._seed_price_history(self, symbols: List[str]) -> None`
    - For each symbol: read cache → if miss or stale call `_fetch_and_cache()` → call `_inject_price_history()` with whatever records are available
    - _Requirements: 4.1, 4.3, 4.4, 4.5_

  - [x] 5.7 Write property test — Property 6: Stale or missing cache triggers a network fetch
    - **Property 6: When `read()` returns `None` or `is_stale()` is `True`, `_seed_price_history()` shall call `fetch_historical()` exactly once per symbol**
    - **Validates: Requirements 3.3, 4.4**

  - [x] 5.8 Write property test — Property 7: Fresh cache skips network fetch
    - **Property 7: When `read()` returns a non-stale `CacheEntry`, `_seed_price_history()` shall not call `fetch_historical()` for that symbol**
    - **Validates: Requirements 4.3**

  - [x] 5.9 Call `_seed_price_history()` at the end of the model-setup block in `CalgoSystem.initialize()`, before `transition_to(READY)`
    - Derive the symbols list from the configured trading symbols (e.g., from `active_models` parameters or a new `symbols` config field)
    - _Requirements: 4.1, 4.2_

- [x] 6. Update `config/config.json` with optional `cache_config` section
  - Add the `cache_config` block with `cache_directory` and `max_age_days` fields to `config/config.json`
  - _Requirements: 6.1, 6.2_

- [x] 7. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests live in `tests/test_historical_data_cache.py` and use Hypothesis (already present in `.hypothesis/`)
- Each property test is tagged with `# Feature: historical-data-cache, Property N: <text>`
- `CacheManager` errors are non-fatal to startup — a cache failure degrades gracefully to the pre-feature behavior
- `_price_history` is written directly (not via `predict()`) to avoid side-effects during seeding
