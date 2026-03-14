# Feature: trading-dashboard, Property 6: Health response contains timestamp
"""
Property-based tests for the Trading Dashboard API.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st

from dashboard_api import app

client = TestClient(app)


# Validates: Requirements 15.2
@settings(max_examples=100)
@given(st.just(None))
def test_health_timestamp_always_present_and_iso8601(_):
    """Property 6: Health response contains timestamp.

    For any call to /api/health, the response SHALL contain a 'timestamp'
    field whose value is a valid ISO 8601 datetime string.
    """
    response = client.get("/api/health")
    assert response.status_code == 200

    body = response.json()
    assert "timestamp" in body, "Health response must contain 'timestamp' field"

    # Validate the timestamp is parseable as ISO 8601
    timestamp_str = body["timestamp"]
    parsed = datetime.fromisoformat(timestamp_str)
    assert isinstance(parsed, datetime), "Timestamp must parse to a datetime object"


# ---------------------------------------------------------------------------
# GET /api/symbols tests
# ---------------------------------------------------------------------------

def test_symbols_returns_list():
    """GET /api/symbols returns a JSON array."""
    response = client.get("/api/symbols")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_symbols_are_uppercase():
    """All returned symbols are uppercase strings."""
    response = client.get("/api/symbols")
    symbols = response.json()
    for symbol in symbols:
        assert symbol == symbol.upper(), f"Symbol {symbol!r} is not uppercase"


def test_symbols_contains_known_cache_files():
    """Known cache files (AAPL, GOOGL, MSFT) appear in the response."""
    response = client.get("/api/symbols")
    symbols = response.json()
    for expected in ["AAPL", "GOOGL", "MSFT"]:
        assert expected in symbols


def test_symbols_no_directory_returns_empty(tmp_path, monkeypatch):
    """If cache/historical/ does not exist, return an empty array."""
    import dashboard_api
    monkeypatch.setattr(dashboard_api, "HISTORICAL_CACHE_DIR", str(tmp_path / "nonexistent"))
    response = client.get("/api/symbols")
    assert response.status_code == 200
    assert response.json() == []


def test_symbols_empty_directory_returns_empty(tmp_path, monkeypatch):
    """If cache/historical/ exists but has no .json files, return an empty array."""
    import dashboard_api
    monkeypatch.setattr(dashboard_api, "HISTORICAL_CACHE_DIR", str(tmp_path))
    response = client.get("/api/symbols")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/dates tests
# ---------------------------------------------------------------------------

def test_dates_returns_all_keys():
    """GET /api/dates returns a JSON object with signals, trades, portfolio, errors keys."""
    response = client.get("/api/dates")
    assert response.status_code == 200
    body = response.json()
    for key in ("signals", "trades", "portfolio", "errors"):
        assert key in body, f"Missing key: {key}"


def test_dates_values_are_lists():
    """Each value in the /api/dates response is a list."""
    response = client.get("/api/dates")
    body = response.json()
    for key, value in body.items():
        assert isinstance(value, list), f"Value for {key!r} is not a list"


def test_dates_descending_order(tmp_path, monkeypatch):
    """Dates are returned in descending order (most recent first)."""
    import dashboard_api

    signals_dir = tmp_path / "signals"
    signals_dir.mkdir()
    for date in ["2026-03-11", "2026-03-13", "2026-03-12"]:
        (signals_dir / f"{date}.json").write_text("[]")

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        "signals": str(signals_dir),
        "trades": str(tmp_path / "trades"),
        "portfolio": str(tmp_path / "portfolio"),
        "errors": str(tmp_path / "errors"),
    })

    response = client.get("/api/dates")
    assert response.status_code == 200
    body = response.json()
    assert body["signals"] == ["2026-03-13", "2026-03-12", "2026-03-11"]


def test_dates_empty_when_no_files(tmp_path, monkeypatch):
    """Empty directories return empty arrays for each log type."""
    import dashboard_api

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        "signals": str(tmp_path / "signals"),
        "trades": str(tmp_path / "trades"),
        "portfolio": str(tmp_path / "portfolio"),
        "errors": str(tmp_path / "errors"),
    })

    response = client.get("/api/dates")
    assert response.status_code == 200
    body = response.json()
    for key in ("signals", "trades", "portfolio", "errors"):
        assert body[key] == []


def test_dates_known_log_files():
    """Known log files (signals/2026-03-13, errors/2026-03-13, errors/2026-03-14) appear in response."""
    response = client.get("/api/dates")
    body = response.json()
    assert "2026-03-13" in body["signals"]
    assert "2026-03-13" in body["errors"]
    assert "2026-03-14" in body["errors"]
    # errors should be descending: 2026-03-14 before 2026-03-13
    assert body["errors"].index("2026-03-14") < body["errors"].index("2026-03-13")


# ---------------------------------------------------------------------------
# Property 5: Dates derived from filenames (Hypothesis)
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 5: Dates derived from filenames
# Validates: Requirements 7.2, 7.3
@settings(max_examples=100)
@given(st.sets(
    st.dates(
        min_value=__import__('datetime').date(2020, 1, 1),
        max_value=__import__('datetime').date(2030, 12, 31),
    ),
    min_size=0,
    max_size=20,
))
def test_dates_match_filenames_descending(date_set):
    """Property 5: /api/dates returns exactly the dates from filenames, descending.

    For any set of YYYY-MM-DD date strings, creating corresponding .json files
    in a temp directory and pointing LOG_DIRS at it should yield exactly those
    dates in descending order.
    """
    import tempfile
    import dashboard_api
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmp:
        import os
        signals_dir = os.path.join(tmp, "signals")
        os.makedirs(signals_dir)
        date_strings = [d.strftime("%Y-%m-%d") for d in date_set]
        for ds in date_strings:
            with open(os.path.join(signals_dir, f"{ds}.json"), "w") as f:
                f.write("[]")

        patched_dirs = {
            "signals": signals_dir,
            "trades": os.path.join(tmp, "trades"),
            "portfolio": os.path.join(tmp, "portfolio"),
            "errors": os.path.join(tmp, "errors"),
        }

        with patch.object(dashboard_api, "LOG_DIRS", patched_dirs):
            response = client.get("/api/dates")

    assert response.status_code == 200
    body = response.json()

    expected = sorted(date_strings, reverse=True)
    assert body["signals"] == expected


# ---------------------------------------------------------------------------
# GET /api/price-history/{symbol} tests
# ---------------------------------------------------------------------------

def test_price_history_returns_data_for_known_symbol():
    """GET /api/price-history/AAPL returns 200 with JSON data."""
    response = client.get("/api/price-history/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "symbol" in data


def test_price_history_uppercases_symbol():
    """GET /api/price-history/aapl (lowercase) returns same data as /api/price-history/AAPL."""
    lower = client.get("/api/price-history/aapl")
    upper = client.get("/api/price-history/AAPL")
    assert lower.status_code == 200
    assert lower.json() == upper.json()


def test_price_history_404_for_missing_symbol():
    """GET /api/price-history/UNKNOWN returns 404 with descriptive message."""
    response = client.get("/api/price-history/UNKNOWN")
    assert response.status_code == 404
    assert "UNKNOWN" in response.json()["detail"]


def test_price_history_500_for_corrupt_file(tmp_path, monkeypatch):
    """GET /api/price-history/BAD returns 500 when the file contains invalid JSON."""
    import dashboard_api

    bad_file = tmp_path / "BAD.json"
    bad_file.write_text("{ not valid json }")
    monkeypatch.setattr(dashboard_api, "HISTORICAL_CACHE_DIR", str(tmp_path))

    response = client.get("/api/price-history/BAD")
    assert response.status_code == 500
    assert "BAD" in response.json()["detail"]


def test_price_history_mixed_case_uppercased(tmp_path, monkeypatch):
    """Symbol is uppercased before file lookup — /api/price-history/Msft resolves to MSFT.json."""
    import dashboard_api
    import json as _json

    data = {"symbol": "MSFT", "records": []}
    (tmp_path / "MSFT.json").write_text(_json.dumps(data))
    monkeypatch.setattr(dashboard_api, "HISTORICAL_CACHE_DIR", str(tmp_path))

    response = client.get("/api/price-history/Msft")
    assert response.status_code == 200
    assert response.json()["symbol"] == "MSFT"


# ---------------------------------------------------------------------------
# Property 1: Symbol case normalization (Hypothesis)
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 1: Symbol case normalization
# Validates: Requirements 1.4, 6.2
@settings(max_examples=100)
@given(st.text(
    alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    min_size=1,
    max_size=6,
))
def test_symbol_case_normalization(symbol):
    """Property 1: Symbol case normalization.

    For any mixed-case symbol string, the /api/price-history/{symbol} endpoint
    SHALL resolve the file using the uppercase version of the symbol.
    """
    import json as _json
    import tempfile
    import os
    import dashboard_api
    from unittest.mock import patch

    upper_symbol = symbol.upper()
    data = {"symbol": upper_symbol, "records": []}

    with tempfile.TemporaryDirectory() as tmp:
        file_path = os.path.join(tmp, f"{upper_symbol}.json")
        with open(file_path, "w") as f:
            _json.dump(data, f)

        with patch.object(dashboard_api, "HISTORICAL_CACHE_DIR", tmp):
            response = client.get(f"/api/price-history/{symbol}")

    assert response.status_code == 200, (
        f"Expected 200 for symbol {symbol!r} (uppercase: {upper_symbol!r}), "
        f"got {response.status_code}"
    )

    body = response.json()
    if "symbol" in body:
        assert body["symbol"] == upper_symbol, (
            f"Response symbol {body['symbol']!r} is not uppercase for input {symbol!r}"
        )


# ---------------------------------------------------------------------------
# GET /api/signals[/{date}] tests
# ---------------------------------------------------------------------------

def test_signals_missing_date_returns_empty():
    """GET /api/signals/{date} with no matching file returns []."""
    response = client.get("/api/signals/9999-01-01")
    assert response.status_code == 200
    assert response.json() == []


def test_signals_today_returns_list():
    """GET /api/signals (no date) returns a JSON array."""
    response = client.get("/api/signals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_signals_known_date_returns_entries(tmp_path, monkeypatch):
    """GET /api/signals/{date} returns entries from the log file."""
    import json as _json
    import dashboard_api

    signals_dir = tmp_path / "signals"
    signals_dir.mkdir()
    entries = [
        {"symbol": "AAPL", "timestamp": "2026-03-13T10:00:00", "recommendation": "buy",
         "confidence": 0.9, "model_id": "m1", "metadata": {}},
        {"symbol": "MSFT", "timestamp": "2026-03-13T09:00:00", "recommendation": "hold",
         "confidence": 0.5, "model_id": "m1", "metadata": {}},
    ]
    (signals_dir / "2026-03-13.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "signals": str(signals_dir),
    })

    response = client.get("/api/signals/2026-03-13")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    # Should be sorted ascending by timestamp
    assert result[0]["timestamp"] < result[1]["timestamp"]


def test_signals_corrupt_file_returns_empty(tmp_path, monkeypatch):
    """GET /api/signals/{date} returns [] when the file contains invalid JSON."""
    import dashboard_api

    signals_dir = tmp_path / "signals"
    signals_dir.mkdir()
    (signals_dir / "2026-03-13.json").write_text("{ not valid json }")

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "signals": str(signals_dir),
    })

    response = client.get("/api/signals/2026-03-13")
    assert response.status_code == 200
    assert response.json() == []


def test_signals_sorted_ascending(tmp_path, monkeypatch):
    """Signals are returned sorted ascending by timestamp."""
    import json as _json
    import dashboard_api

    signals_dir = tmp_path / "signals"
    signals_dir.mkdir()
    entries = [
        {"symbol": "A", "timestamp": "2026-03-13T12:00:00", "recommendation": "buy",
         "confidence": 0.8, "model_id": "m1", "metadata": {}},
        {"symbol": "B", "timestamp": "2026-03-13T08:00:00", "recommendation": "sell",
         "confidence": 0.7, "model_id": "m1", "metadata": {}},
        {"symbol": "C", "timestamp": "2026-03-13T10:00:00", "recommendation": "hold",
         "confidence": 0.6, "model_id": "m1", "metadata": {}},
    ]
    (signals_dir / "2026-03-13.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "signals": str(signals_dir),
    })

    response = client.get("/api/signals/2026-03-13")
    result = response.json()
    timestamps = [e["timestamp"] for e in result]
    assert timestamps == sorted(timestamps)


# ---------------------------------------------------------------------------
# GET /api/trades[/{date}] tests
# ---------------------------------------------------------------------------

def test_trades_missing_date_returns_empty():
    """GET /api/trades/{date} with no matching file returns []."""
    response = client.get("/api/trades/9999-01-01")
    assert response.status_code == 200
    assert response.json() == []


def test_trades_today_returns_list():
    """GET /api/trades (no date) returns a JSON array."""
    response = client.get("/api/trades")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trades_known_date_returns_entries(tmp_path, monkeypatch):
    """GET /api/trades/{date} returns entries from the log file sorted by timestamp."""
    import json as _json
    import dashboard_api

    trades_dir = tmp_path / "trades"
    trades_dir.mkdir()
    entries = [
        {"symbol": "AAPL", "timestamp": "2026-03-13T15:00:00", "side": "buy", "qty": 10},
        {"symbol": "MSFT", "timestamp": "2026-03-13T11:00:00", "side": "sell", "qty": 5},
    ]
    (trades_dir / "2026-03-13.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "trades": str(trades_dir),
    })

    response = client.get("/api/trades/2026-03-13")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert result[0]["timestamp"] < result[1]["timestamp"]


def test_trades_corrupt_file_returns_empty(tmp_path, monkeypatch):
    """GET /api/trades/{date} returns [] when the file contains invalid JSON."""
    import dashboard_api

    trades_dir = tmp_path / "trades"
    trades_dir.mkdir()
    (trades_dir / "2026-03-13.json").write_text("not json at all")

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "trades": str(trades_dir),
    })

    response = client.get("/api/trades/2026-03-13")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Property 2: Missing file returns safe default (Hypothesis)
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 2: Missing file returns safe default
# Validates: Requirements 2.3, 3.3
@settings(max_examples=100)
@given(st.dates(
    min_value=__import__('datetime').date(2030, 1, 1),
    max_value=__import__('datetime').date(2099, 12, 31),
))
def test_missing_log_file_returns_empty_array(date):
    """Property 2: Missing file returns safe default.

    For any date string for which no log file exists, the signals and trades
    endpoints SHALL return an empty JSON array (not a 4xx or 5xx error).
    """
    date_str = date.strftime("%Y-%m-%d")
    for endpoint in (f"/api/signals/{date_str}", f"/api/trades/{date_str}"):
        response = client.get(endpoint)
        assert response.status_code == 200, (
            f"Expected 200 for {endpoint}, got {response.status_code}"
        )
        assert response.json() == [], (
            f"Expected [] for {endpoint}, got {response.json()!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Timestamp sort order (Hypothesis)
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 3: Timestamp sort order
# Validates: Requirements 2.4, 3.4
@settings(max_examples=100)
@given(st.lists(
    st.fixed_dictionaries({
        "symbol": st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=5),
        "timestamp": st.datetimes(
            min_value=__import__('datetime').datetime(2020, 1, 1),
            max_value=__import__('datetime').datetime(2030, 12, 31),
        ).map(lambda dt: dt.isoformat()),
        "recommendation": st.sampled_from(["buy", "sell", "hold"]),
        "confidence": st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        "model_id": st.just("test_model"),
        "metadata": st.just({}),
    }),
    min_size=1,
    max_size=20,
))
def test_signals_timestamp_sort_order(entries):
    """Property 3: Timestamp sort order.

    For any non-empty signals log file, the entries returned by the API SHALL
    be sorted in ascending timestamp order.
    """
    import json as _json
    import tempfile
    import os
    import dashboard_api
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmp:
        signals_dir = os.path.join(tmp, "signals")
        os.makedirs(signals_dir)
        with open(os.path.join(signals_dir, "2025-01-01.json"), "w") as f:
            _json.dump(entries, f)

        patched_dirs = {**dashboard_api.LOG_DIRS, "signals": signals_dir}
        with patch.object(dashboard_api, "LOG_DIRS", patched_dirs):
            response = client.get("/api/signals/2025-01-01")

    assert response.status_code == 200
    result = response.json()
    timestamps = [e["timestamp"] for e in result]
    assert timestamps == sorted(timestamps), (
        f"Timestamps not sorted ascending: {timestamps}"
    )


# ---------------------------------------------------------------------------
# GET /api/portfolio[/{date}] tests
# ---------------------------------------------------------------------------

def test_portfolio_missing_date_returns_empty():
    """GET /api/portfolio/{date} with no matching file returns []."""
    response = client.get("/api/portfolio/9999-01-01")
    assert response.status_code == 200
    assert response.json() == []


def test_portfolio_today_returns_list():
    """GET /api/portfolio (no date) returns a JSON array."""
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_portfolio_known_date_returns_entries(tmp_path, monkeypatch):
    """GET /api/portfolio/{date} returns entries sorted ascending by timestamp."""
    import json as _json
    import dashboard_api

    portfolio_dir = tmp_path / "portfolio"
    portfolio_dir.mkdir()
    entries = [
        {"timestamp": "2026-03-13T15:00:00", "total_value": 10500.0, "positions": {}},
        {"timestamp": "2026-03-13T09:00:00", "total_value": 10000.0, "positions": {}},
    ]
    (portfolio_dir / "2026-03-13.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "portfolio": str(portfolio_dir),
    })

    response = client.get("/api/portfolio/2026-03-13")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert result[0]["timestamp"] < result[1]["timestamp"]


def test_portfolio_corrupt_file_returns_empty(tmp_path, monkeypatch):
    """GET /api/portfolio/{date} returns [] when the file contains invalid JSON."""
    import dashboard_api

    portfolio_dir = tmp_path / "portfolio"
    portfolio_dir.mkdir()
    (portfolio_dir / "2026-03-13.json").write_text("not json at all")

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "portfolio": str(portfolio_dir),
    })

    response = client.get("/api/portfolio/2026-03-13")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/logs[/{date}] tests
# ---------------------------------------------------------------------------

def test_logs_missing_date_returns_empty():
    """GET /api/logs/{date} with no matching file returns []."""
    response = client.get("/api/logs/9999-01-01")
    assert response.status_code == 200
    assert response.json() == []


def test_logs_today_returns_list():
    """GET /api/logs (no date) returns a JSON array."""
    response = client.get("/api/logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_logs_known_date_returns_entries(tmp_path, monkeypatch):
    """GET /api/logs/{date} returns entries from the errors log file sorted by timestamp."""
    import json as _json
    import dashboard_api

    errors_dir = tmp_path / "errors"
    errors_dir.mkdir()
    entries = [
        {"timestamp": "2026-03-14T10:00:00", "severity": "INFO", "component": "CalgoSystem", "message": "Started"},
        {"timestamp": "2026-03-14T08:00:00", "severity": "ERROR", "component": "CalgoSystem", "message": "Failed"},
    ]
    (errors_dir / "2026-03-14.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "errors": str(errors_dir),
    })

    response = client.get("/api/logs/2026-03-14")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert result[0]["timestamp"] < result[1]["timestamp"]


def test_logs_severity_filter(tmp_path, monkeypatch):
    """GET /api/logs/{date}?severity=WARNING returns only WARNING entries."""
    import json as _json
    import dashboard_api

    errors_dir = tmp_path / "errors"
    errors_dir.mkdir()
    entries = [
        {"timestamp": "2026-03-14T08:00:00", "severity": "INFO", "component": "C", "message": "a"},
        {"timestamp": "2026-03-14T09:00:00", "severity": "WARNING", "component": "C", "message": "b"},
        {"timestamp": "2026-03-14T10:00:00", "severity": "ERROR", "component": "C", "message": "c"},
        {"timestamp": "2026-03-14T11:00:00", "severity": "WARNING", "component": "C", "message": "d"},
    ]
    (errors_dir / "2026-03-14.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "errors": str(errors_dir),
    })

    response = client.get("/api/logs/2026-03-14?severity=WARNING")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    assert all(e["severity"] == "WARNING" for e in result)


def test_logs_no_severity_filter_returns_all(tmp_path, monkeypatch):
    """GET /api/logs/{date} without severity param returns all entries."""
    import json as _json
    import dashboard_api

    errors_dir = tmp_path / "errors"
    errors_dir.mkdir()
    entries = [
        {"timestamp": "2026-03-14T08:00:00", "severity": "INFO", "component": "C", "message": "a"},
        {"timestamp": "2026-03-14T09:00:00", "severity": "WARNING", "component": "C", "message": "b"},
        {"timestamp": "2026-03-14T10:00:00", "severity": "ERROR", "component": "C", "message": "c"},
    ]
    (errors_dir / "2026-03-14.json").write_text(_json.dumps(entries))

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "errors": str(errors_dir),
    })

    response = client.get("/api/logs/2026-03-14")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_logs_corrupt_file_returns_empty(tmp_path, monkeypatch):
    """GET /api/logs/{date} returns [] when the file contains invalid JSON."""
    import dashboard_api

    errors_dir = tmp_path / "errors"
    errors_dir.mkdir()
    (errors_dir / "2026-03-14.json").write_text("{ bad json }")

    monkeypatch.setattr(dashboard_api, "LOG_DIRS", {
        **dashboard_api.LOG_DIRS,
        "errors": str(errors_dir),
    })

    response = client.get("/api/logs/2026-03-14")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Property 2 extension: portfolio and logs also return [] for missing files
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 2: Missing file returns safe default
# Validates: Requirements 4.3, 5.3
@settings(max_examples=100)
@given(st.dates(
    min_value=__import__('datetime').date(2030, 1, 1),
    max_value=__import__('datetime').date(2099, 12, 31),
))
def test_missing_log_file_returns_empty_array_portfolio_logs(date):
    """Property 2 (portfolio/logs): Missing file returns safe default.

    For any date string for which no log file exists, the portfolio and logs
    endpoints SHALL return an empty JSON array (not a 4xx or 5xx error).
    """
    date_str = date.strftime("%Y-%m-%d")
    for endpoint in (f"/api/portfolio/{date_str}", f"/api/logs/{date_str}"):
        response = client.get(endpoint)
        assert response.status_code == 200, (
            f"Expected 200 for {endpoint}, got {response.status_code}"
        )
        assert response.json() == [], (
            f"Expected [] for {endpoint}, got {response.json()!r}"
        )


# ---------------------------------------------------------------------------
# Property 4: Severity filter is a subset (Hypothesis)
# ---------------------------------------------------------------------------

# Feature: trading-dashboard, Property 4: Severity filter is a subset
# Validates: Requirements 5.4
@settings(max_examples=100)
@given(st.lists(
    st.fixed_dictionaries({
        "timestamp": st.datetimes(
            min_value=__import__('datetime').datetime(2020, 1, 1),
            max_value=__import__('datetime').datetime(2030, 12, 31),
        ).map(lambda dt: dt.isoformat()),
        "severity": st.sampled_from(["INFO", "WARNING", "ERROR"]),
        "component": st.just("TestComponent"),
        "message": st.text(min_size=1, max_size=50),
    }),
    min_size=1,
    max_size=20,
))
def test_severity_filter_is_subset(entries):
    """Property 4: Severity filter is a subset.

    For any date and any severity value s, the entries returned by
    /api/logs/{date}?severity=s SHALL be a subset of the unfiltered entries,
    and every entry in the filtered result SHALL have severity == s.
    """
    import json as _json
    import tempfile
    import os
    import dashboard_api
    from unittest.mock import patch

    with tempfile.TemporaryDirectory() as tmp:
        errors_dir = os.path.join(tmp, "errors")
        os.makedirs(errors_dir)
        with open(os.path.join(errors_dir, "2025-01-01.json"), "w") as f:
            _json.dump(entries, f)

        patched_dirs = {**dashboard_api.LOG_DIRS, "errors": errors_dir}
        with patch.object(dashboard_api, "LOG_DIRS", patched_dirs):
            unfiltered = client.get("/api/logs/2025-01-01").json()
            for sev in ("INFO", "WARNING", "ERROR"):
                filtered = client.get(f"/api/logs/2025-01-01?severity={sev}").json()

    # Every filtered entry must have the correct severity
    assert all(e["severity"] == sev for e in filtered), (
        f"Filtered entries contain wrong severity for {sev!r}: {filtered}"
    )
    # Filtered must be a subset of unfiltered (by content)
    unfiltered_set = [e for e in unfiltered if e.get("severity") == sev]
    assert filtered == unfiltered_set, (
        f"Filtered result for {sev!r} is not the expected subset"
    )
