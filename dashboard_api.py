"""
Trading Dashboard API Server

FastAPI application that reads calgo's on-disk data files and exposes them
as REST endpoints. All routes are prefixed with /api.
"""

import json
import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Trading Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# File reading helpers
# ---------------------------------------------------------------------------

def read_json_file(path):
    """Read and parse a JSON file.

    Returns None if the file is missing (FileNotFoundError).
    Raises json.JSONDecodeError if the file exists but contains invalid JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def list_dated_files(log_dir):
    """Scan a logs/ subdirectory and return sorted date strings.

    Derives date strings from {date}.json filenames (e.g. "2026-03-13" from
    "2026-03-13.json"). Returns an empty list if the directory doesn't exist.
    """
    if not os.path.isdir(log_dir):
        return []
    dates = []
    for filename in os.listdir(log_dir):
        if filename.endswith(".json"):
            date_str = filename[:-5]  # strip ".json"
            dates.append(date_str)
    return sorted(dates)


def sort_by_timestamp(entries):
    """Sort a list of dicts by their 'timestamp' field ascending.

    Entries missing the 'timestamp' key are sorted to the end.
    """
    return sorted(entries, key=lambda e: (e.get("timestamp") is None, e.get("timestamp") or ""))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    """Return server health status with current ISO 8601 timestamp."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# Symbols
# ---------------------------------------------------------------------------

HISTORICAL_CACHE_DIR = "cache/historical"


@app.get("/api/symbols")
def list_symbols():
    """Return a sorted JSON array of uppercase symbol names from cache/historical/."""
    if not os.path.isdir(HISTORICAL_CACHE_DIR):
        return []
    symbols = []
    for filename in os.listdir(HISTORICAL_CACHE_DIR):
        if filename.endswith(".json"):
            symbols.append(filename[:-5].upper())
    return sorted(symbols)


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

LOG_DIRS = {
    "signals": "logs/signals",
    "trades": "logs/trades",
    "portfolio": "logs/portfolio",
    "errors": "logs/errors",
}


@app.get("/api/price-history/{symbol}")
def get_price_history(symbol: str):
    """Return full price history JSON for the given symbol from cache/historical/{SYMBOL}.json."""
    symbol = symbol.upper()
    path = os.path.join(HISTORICAL_CACHE_DIR, f"{symbol}.json")
    try:
        data = read_json_file(path)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Failed to parse price data for '{symbol}'")
    if data is None:
        raise HTTPException(status_code=404, detail=f"No price data found for symbol '{symbol}'")
    return data


@app.get("/api/dates")
def list_dates():
    """Return available log dates per log type, sorted descending (most recent first)."""
    return {
        key: list(reversed(list_dated_files(log_dir)))
        for key, log_dir in LOG_DIRS.items()
    }


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

import logging as _logging

_logger = _logging.getLogger(__name__)


@app.get("/api/signals")
def get_signals_today():
    """Return Signal entries for today's date."""
    return _get_log_entries("signals", datetime.now().strftime("%Y-%m-%d"))


@app.get("/api/signals/{date}")
def get_signals(date: str):
    """Return Signal entries for the given date, sorted ascending by timestamp."""
    return _get_log_entries("signals", date)


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------

@app.get("/api/trades")
def get_trades_today():
    """Return Trade entries for today's date."""
    return _get_log_entries("trades", datetime.now().strftime("%Y-%m-%d"))


@app.get("/api/trades/{date}")
def get_trades(date: str):
    """Return Trade entries for the given date, sorted ascending by timestamp."""
    return _get_log_entries("trades", date)


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

@app.get("/api/portfolio")
def get_portfolio_today():
    """Return Portfolio_Snapshot entries for today's date."""
    return _get_log_entries("portfolio", datetime.now().strftime("%Y-%m-%d"))


@app.get("/api/portfolio/{date}")
def get_portfolio(date: str):
    """Return Portfolio_Snapshot entries for the given date, sorted ascending by timestamp."""
    return _get_log_entries("portfolio", date)


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

@app.get("/api/logs")
def get_logs_today(severity: Optional[str] = Query(default=None)):
    """Return Log_Entry records for today's date, optionally filtered by severity."""
    return _get_log_entries_filtered("errors", datetime.now().strftime("%Y-%m-%d"), severity)


@app.get("/api/logs/{date}")
def get_logs(date: str, severity: Optional[str] = Query(default=None)):
    """Return Log_Entry records for the given date, optionally filtered by severity."""
    return _get_log_entries_filtered("errors", date, severity)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _get_log_entries(log_type: str, date: str):
    """Read a dated log file and return entries sorted by timestamp.

    Returns [] if the file is missing or contains corrupt JSON.
    """
    path = os.path.join(LOG_DIRS[log_type], f"{date}.json")
    try:
        data = read_json_file(path)
    except json.JSONDecodeError:
        _logger.warning("Corrupt log file: %s", path)
        return []
    if data is None:
        return []
    return sort_by_timestamp(data)


def _get_log_entries_filtered(log_type: str, date: str, severity: Optional[str]):
    """Read a dated log file, optionally filter by severity, and return sorted entries.

    Returns [] if the file is missing or contains corrupt JSON.
    """
    entries = _get_log_entries(log_type, date)
    if severity is not None:
        entries = [e for e in entries if e.get("severity") == severity]
    return entries
