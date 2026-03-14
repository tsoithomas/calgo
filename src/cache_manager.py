"""Cache manager for historical price data"""
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.config_models import CacheConfig
from src.models import PriceData
from src.result import Result


class CacheError(Exception):
    """Raised when a cache read or write operation fails"""
    pass


@dataclass
class CacheEntry:
    """A cached set of price records for a single symbol"""
    symbol: str
    fetched_at: datetime
    records: List[PriceData]


class CacheManager:
    """Reads and writes per-symbol JSON cache files to disk"""

    def __init__(self, config: CacheConfig) -> None:
        cache_dir = config.cache_directory
        if os.path.exists(cache_dir) and not os.path.isdir(cache_dir):
            raise CacheError(
                f"Cache directory path '{cache_dir}' exists but is not a directory"
            )
        if os.path.isdir(cache_dir) and not os.access(cache_dir, os.R_OK | os.W_OK):
            raise CacheError(
                f"Cache directory '{cache_dir}' is not readable/writable"
            )
        self._config = config

    def read(self, symbol: str) -> Result[Optional[CacheEntry], CacheError]:
        """Return CacheEntry if file exists and is parseable, None on miss, Err on corrupt."""
        from decimal import Decimal
        from src.models import DataSource

        file_path = os.path.join(self._config.cache_directory, f"{symbol.upper()}.json")

        if not os.path.exists(file_path):
            return Result.ok(None)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            fetched_at = datetime.fromisoformat(data["fetched_at"])

            records = []
            for r in data["records"]:
                records.append(
                    PriceData(
                        symbol=r["symbol"],
                        timestamp=datetime.fromisoformat(r["timestamp"]),
                        open=Decimal(r["open"]),
                        high=Decimal(r["high"]),
                        low=Decimal(r["low"]),
                        close=Decimal(r["close"]),
                        volume=int(r["volume"]),
                        source=DataSource(r["source"]),
                    )
                )

            records.sort(key=lambda rec: rec.timestamp)

            return Result.ok(CacheEntry(symbol=data["symbol"], fetched_at=fetched_at, records=records))

        except (KeyError, ValueError, json.JSONDecodeError, OSError) as exc:
            return Result.err(CacheError(f"Failed to read cache for '{symbol}': {exc}"))

    def write(self, symbol: str, records: List[PriceData]) -> Result[None, CacheError]:
        """Serialize records to disk, creating directories as needed."""
        cache_dir = self._config.cache_directory
        file_path = os.path.join(cache_dir, f"{symbol.upper()}.json")

        # Build the JSON payload
        payload = {
            "symbol": symbol,
            "fetched_at": datetime.now().isoformat(),
            "record_count": len(records),
            "records": [
                {
                    "symbol": r.symbol,
                    "timestamp": r.timestamp.isoformat(),
                    "open": str(r.open),
                    "high": str(r.high),
                    "low": str(r.low),
                    "close": str(r.close),
                    "volume": r.volume,
                    "source": r.source.value,
                }
                for r in records
            ],
        }

        try:
            os.makedirs(cache_dir, exist_ok=True)

            # Write to a temp file in the same directory, then atomically rename
            dir_fd = os.path.dirname(file_path) or "."
            tmp_path = None
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=dir_fd,
                delete=False,
                suffix=".tmp",
            ) as tmp:
                tmp_path = tmp.name
                json.dump(payload, tmp, ensure_ascii=False, indent=2)

            os.replace(tmp_path, file_path)
        except OSError as exc:
            # Clean up temp file if it was created
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            return Result.err(CacheError(f"Failed to write cache for '{symbol}': {exc}"))

        return Result.ok(None)

    def is_stale(self, entry: CacheEntry) -> bool:
        """True when the most recent record's date is before today, or entry is empty."""
        from datetime import date, timedelta

        if not entry.records:
            return True

        most_recent_date = entry.records[-1].timestamp.date()
        return date.today() - most_recent_date > timedelta(days=self._config.max_age_days)
