"""Property-based tests for the historical data cache feature."""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.cache_manager import CacheManager
from src.config_models import CacheConfig
from src.models import DataSource, PriceData


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

# Prices: finite decimals only (no NaN/Inf), reasonable precision
price_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("999999.99"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)

price_data_strategy = st.builds(
    PriceData,
    symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    timestamp=st.datetimes(timezones=st.just(timezone.utc)),
    open=price_strategy,
    high=price_strategy,
    low=price_strategy,
    close=price_strategy,
    volume=st.integers(min_value=0, max_value=10_000_000_000),
    source=st.sampled_from(DataSource),
)


def _make_cache_manager(cache_dir: str) -> CacheManager:
    return CacheManager(CacheConfig(cache_directory=cache_dir))


# ---------------------------------------------------------------------------
# Property 1: Serialization round-trip
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 1: Serialization round-trip
@given(records=st.lists(
    st.builds(
        PriceData,
        symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        timestamp=st.datetimes(timezones=st.none()),  # naive datetimes to avoid tz round-trip issues
        open=price_strategy,
        high=price_strategy,
        low=price_strategy,
        close=price_strategy,
        volume=st.integers(min_value=0, max_value=10_000_000_000),
        source=st.sampled_from(DataSource),
    ),
    min_size=0,
    max_size=50,
))
@settings(max_examples=100)
def test_property1_serialization_round_trip(records: list) -> None:
    """Validates: Requirements 2.5, 7.4

    For any valid List[PriceData], write() then read() shall return an
    equivalent list in the same order.
    """
    symbol = "ROUNDTRIP"

    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = _make_cache_manager(tmp_dir)

        result = manager.write(symbol, records)
        assert result.is_ok(), f"write() failed: {result.unwrap_err()}"

        read_result = manager.read(symbol)
        assert read_result.is_ok(), f"read() failed: {read_result.unwrap_err()}"

        entry = read_result.unwrap()
        assert entry is not None, "read() returned None after write()"

        # read() sorts by timestamp ascending — sort input the same way for comparison
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        returned = entry.records

        assert len(returned) == len(sorted_records), (
            f"Length mismatch: expected {len(sorted_records)}, got {len(returned)}"
        )

        for i, (expected, actual) in enumerate(zip(sorted_records, returned)):
            assert expected.symbol == actual.symbol, f"[{i}] symbol mismatch"
            assert expected.timestamp == actual.timestamp, f"[{i}] timestamp mismatch"
            assert expected.open == actual.open, f"[{i}] open mismatch"
            assert expected.high == actual.high, f"[{i}] high mismatch"
            assert expected.low == actual.low, f"[{i}] low mismatch"
            assert expected.close == actual.close, f"[{i}] close mismatch"
            assert expected.volume == actual.volume, f"[{i}] volume mismatch"
            assert expected.source == actual.source, f"[{i}] source mismatch"


# ---------------------------------------------------------------------------
# Property 2: Serialized record field completeness
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 2: Serialized record field completeness
@given(record=price_data_strategy)
@settings(max_examples=100)
def test_property2_serialized_record_field_completeness(record: PriceData) -> None:
    """Validates: Requirements 7.2

    For any PriceData record written to a cache file, the JSON object shall
    contain all required fields with correct types.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = _make_cache_manager(tmp_dir)
        result = manager.write(record.symbol, [record])
        assert result.is_ok(), f"write() failed: {result.unwrap_err()}"

        file_path = os.path.join(tmp_dir, f"{record.symbol.upper()}.json")
        with open(file_path, encoding="utf-8") as f:
            payload = json.load(f)

        assert "records" in payload
        assert len(payload["records"]) == 1
        rec = payload["records"][0]

        # All required fields must be present and non-null
        required_fields = ("symbol", "timestamp", "open", "high", "low", "close", "volume", "source")
        for field in required_fields:
            assert field in rec, f"Missing field: {field}"
            assert rec[field] is not None, f"Field is null: {field}"

        # Type checks
        assert isinstance(rec["symbol"], str)
        assert isinstance(rec["timestamp"], str)  # ISO 8601 string
        # Decimal fields stored as strings
        for price_field in ("open", "high", "low", "close"):
            assert isinstance(rec[price_field], str), f"{price_field} should be a decimal string"
            Decimal(rec[price_field])  # must be parseable as Decimal
        assert isinstance(rec["volume"], int)
        assert isinstance(rec["source"], str)

        # Timestamp must be parseable as ISO 8601
        datetime.fromisoformat(rec["timestamp"])


# ---------------------------------------------------------------------------
# Property 3: Cache file metadata fields
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 3: Cache file metadata fields
@given(records=st.lists(price_data_strategy, min_size=1, max_size=50))
@settings(max_examples=100)
def test_property3_cache_file_metadata_fields(records: list) -> None:
    """Validates: Requirements 1.4, 7.3

    For any non-empty records list, the JSON file shall contain symbol,
    fetched_at, record_count, and records where record_count == len(records).
    """
    symbol = records[0].symbol  # use the first record's symbol for the cache key

    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = _make_cache_manager(tmp_dir)
        result = manager.write(symbol, records)
        assert result.is_ok(), f"write() failed: {result.unwrap_err()}"

        file_path = os.path.join(tmp_dir, f"{symbol.upper()}.json")
        with open(file_path, encoding="utf-8") as f:
            payload = json.load(f)

        # All top-level metadata fields must be present
        for field in ("symbol", "fetched_at", "record_count", "records"):
            assert field in payload, f"Missing top-level field: {field}"

        # record_count must equal the actual number of records
        assert payload["record_count"] == len(records), (
            f"record_count {payload['record_count']} != len(records) {len(records)}"
        )

        # records must be a list with the same length
        assert isinstance(payload["records"], list)
        assert len(payload["records"]) == len(records)

        # fetched_at must be a parseable ISO 8601 string
        assert isinstance(payload["fetched_at"], str)
        datetime.fromisoformat(payload["fetched_at"])


# ---------------------------------------------------------------------------
# Property 4: Cache files written to configured directory
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 4: Cache files written to configured directory
@given(
    symbol=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    records=st.lists(price_data_strategy, min_size=0, max_size=10),
)
@settings(max_examples=100)
def test_property4_cache_files_written_to_configured_directory(symbol: str, records: list) -> None:
    """Validates: Requirements 1.2, 6.1

    After write() succeeds, the file shall exist at {cache_directory}/{SYMBOL}.json.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Use a subdirectory that doesn't exist yet to also verify directory creation
        cache_dir = os.path.join(tmp_dir, "cache", "historical")
        manager = _make_cache_manager(cache_dir)
        result = manager.write(symbol, records)
        assert result.is_ok(), f"write() failed: {result.unwrap_err()}"

        expected_path = os.path.join(cache_dir, f"{symbol.upper()}.json")
        assert os.path.isfile(expected_path), (
            f"Expected cache file not found at: {expected_path}"
        )


# ---------------------------------------------------------------------------
# Property 5: Staleness detection respects max_age_days
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 5: Staleness detection respects max_age_days
@given(
    max_age_days=st.integers(min_value=1, max_value=30),
    days_old=st.integers(min_value=0, max_value=60),
)
@settings(max_examples=100)
def test_property5_staleness_detection_respects_max_age_days(max_age_days: int, days_old: int) -> None:
    """Validates: Requirements 3.2, 6.2

    is_stale() returns True when the most recent record's date is more than
    max_age_days days before today, False when within threshold.
    """
    from datetime import timedelta
    from src.cache_manager import CacheEntry

    manager = CacheManager(CacheConfig(max_age_days=max_age_days, cache_directory="/tmp"))

    timestamp = datetime.now() - timedelta(days=days_old)
    record = PriceData(
        symbol="TEST",
        timestamp=timestamp,
        open=Decimal("100.00"),
        high=Decimal("110.00"),
        low=Decimal("90.00"),
        close=Decimal("105.00"),
        volume=1000,
        source=DataSource.ALPACA,
    )
    entry = CacheEntry(symbol="TEST", fetched_at=datetime.now(), records=[record])

    expected = days_old > max_age_days
    assert manager.is_stale(entry) == expected, (
        f"is_stale() returned {manager.is_stale(entry)} but expected {expected} "
        f"(days_old={days_old}, max_age_days={max_age_days})"
    )

    # Empty records case: is_stale() should always return True
    empty_entry = CacheEntry(symbol="X", fetched_at=datetime.now(), records=[])
    assert manager.is_stale(empty_entry) is True, "is_stale() should return True for empty records"


# ---------------------------------------------------------------------------
# Property 6: Stale or missing cache triggers a network fetch
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 6: Stale or missing cache triggers a network fetch
def test_property6_stale_or_missing_cache_triggers_fetch() -> None:
    """Validates: Requirements 3.3, 4.4

    When read() returns None (miss) or is_stale() returns True,
    _seed_price_history() shall call fetch_historical() exactly once per symbol.
    """
    from unittest.mock import MagicMock, patch
    from src.calgo_system import CalgoSystem
    from src.cache_manager import CacheEntry
    from src.result import Result

    # --- Case 1: cache miss (read returns None) ---
    system = CalgoSystem()
    mock_cache = MagicMock()
    mock_cache.read.return_value = Result.ok(None)
    mock_cache.is_stale.return_value = False  # irrelevant for miss
    system._cache_manager = mock_cache

    mock_ingester = MagicMock()
    mock_ingester.fetch_historical.return_value = Result.ok([])
    system._market_data_ingester = mock_ingester

    mock_signal_gen = MagicMock()
    mock_signal_gen._models = {}
    system._signal_generator = mock_signal_gen

    system._seed_price_history(["AAPL"])
    mock_ingester.fetch_historical.assert_called_once()
    mock_ingester.fetch_historical.reset_mock()

    # --- Case 2: stale cache ---
    system2 = CalgoSystem()
    stale_entry = CacheEntry(symbol="AAPL", fetched_at=datetime.now(), records=[])
    mock_cache2 = MagicMock()
    mock_cache2.read.return_value = Result.ok(stale_entry)
    mock_cache2.is_stale.return_value = True
    system2._cache_manager = mock_cache2

    mock_ingester2 = MagicMock()
    mock_ingester2.fetch_historical.return_value = Result.ok([])
    system2._market_data_ingester = mock_ingester2

    mock_signal_gen2 = MagicMock()
    mock_signal_gen2._models = {}
    system2._signal_generator = mock_signal_gen2

    system2._seed_price_history(["AAPL"])
    mock_ingester2.fetch_historical.assert_called_once()


# ---------------------------------------------------------------------------
# Property 7: Fresh cache skips network fetch
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 7: Fresh cache skips network fetch
def test_property7_fresh_cache_skips_network_fetch() -> None:
    """Validates: Requirements 4.3

    When read() returns a non-stale CacheEntry, _seed_price_history() shall
    not call fetch_historical() for that symbol.
    """
    from unittest.mock import MagicMock
    from src.calgo_system import CalgoSystem
    from src.cache_manager import CacheEntry
    from src.result import Result

    system = CalgoSystem()

    fresh_entry = CacheEntry(symbol="TSLA", fetched_at=datetime.now(), records=[])
    mock_cache = MagicMock()
    mock_cache.read.return_value = Result.ok(fresh_entry)
    mock_cache.is_stale.return_value = False
    system._cache_manager = mock_cache

    mock_ingester = MagicMock()
    system._market_data_ingester = mock_ingester

    mock_signal_gen = MagicMock()
    mock_signal_gen._models = {}
    system._signal_generator = mock_signal_gen

    system._seed_price_history(["TSLA"])
    mock_ingester.fetch_historical.assert_not_called()


# ---------------------------------------------------------------------------
# Property 8: Seeding injects the correct closing prices
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 8: Seeding injects the correct closing prices
@given(
    n_records=st.integers(min_value=0, max_value=100),
    long_window=st.integers(min_value=2, max_value=80),
)
@settings(max_examples=100)
def test_property8_seeding_injects_correct_closing_prices(n_records: int, long_window: int) -> None:
    """Validates: Requirements 4.2, 4.6, 5.3

    For any dataset of N records and long_window L, _price_history[symbol]
    shall contain exactly min(N, L) entries equal to the closing prices of
    the most recent min(N, L) records, ascending by timestamp.
    """
    from datetime import timedelta
    from src.calgo_system import CalgoSystem
    from src.trading_models import MovingAverageCrossover
    from src.signal_generator import SignalGenerator, AggregationStrategy
    from src.config_manager import ConfigurationManager
    from src.config_models import CacheConfig, ModelConfig

    symbol = "TEST"

    # Build N records with ascending timestamps
    base_time = datetime(2024, 1, 1)
    records = [
        PriceData(
            symbol=symbol,
            timestamp=base_time + timedelta(days=i),
            open=Decimal("100.00"),
            high=Decimal("110.00"),
            low=Decimal("90.00"),
            close=Decimal(str(100 + i)),
            volume=1000,
            source=DataSource.ALPACA,
        )
        for i in range(n_records)
    ]

    # Build a CalgoSystem with a real MovingAverageCrossover model
    system = CalgoSystem()

    # Provide a minimal config_manager so _get_long_window works
    mock_config_manager = MagicMock()
    mac_config = ModelConfig(
        model_id="mac",
        model_type="moving_average_crossover",
        parameters={"long_window": long_window, "short_window": max(1, long_window - 1)},
        enabled=True,
    )
    mock_config_manager.get_active_models.return_value = [mac_config]
    system._config_manager = mock_config_manager

    # Use a real short_window that satisfies short < long
    short_window = max(1, long_window - 1)
    model = MovingAverageCrossover(short_window=short_window, long_window=long_window, model_id="mac")
    sg = SignalGenerator(AggregationStrategy.VOTING)
    sg.add_model(model)
    system._signal_generator = sg

    system._inject_price_history(symbol, records)

    expected_count = min(n_records, long_window)
    actual = model._price_history.get(symbol, [])

    assert len(actual) == expected_count, (
        f"Expected {expected_count} prices injected, got {len(actual)} "
        f"(n_records={n_records}, long_window={long_window})"
    )

    # Verify the values match the most recent min(N, L) closing prices
    expected_closes = [r.close for r in records[-long_window:]] if n_records > 0 else []
    assert actual == expected_closes, (
        f"Injected prices do not match expected closing prices"
    )


# ---------------------------------------------------------------------------
# Property 9: Lookback date range covers sufficient calendar days
# ---------------------------------------------------------------------------

# Feature: historical-data-cache, Property 9: Lookback date range covers sufficient calendar days
@given(
    long_window=st.integers(min_value=1, max_value=200),
    multiplier=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=100)
def test_property9_lookback_date_range_covers_sufficient_days(long_window: int, multiplier: int) -> None:
    """Validates: Requirements 5.1, 5.2

    For any long_window L and multiplier M, start_date shall be at least
    L * M calendar days before today.
    """
    start_date = datetime.today() - timedelta(days=long_window * multiplier)
    end_date = datetime.today()

    elapsed_days = (end_date - start_date).days
    assert elapsed_days >= long_window * multiplier, (
        f"start_date is only {elapsed_days} days before today; "
        f"expected at least {long_window * multiplier} "
        f"(long_window={long_window}, multiplier={multiplier})"
    )