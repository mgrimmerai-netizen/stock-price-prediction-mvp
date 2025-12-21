from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# -----------------------------
# Config / constants
# -----------------------------
STOOQ_BASE = "https://stooq.com/q/d/l"
RAW_DIR = Path("data/raw")
PRICES_DIR = RAW_DIR / "prices"
MANIFEST_PATH = RAW_DIR / "manifest.csv"



@dataclass(fronzen=True)
class DownloadResult:
  ticker: str
  stooq_symbol: str
  status: str # "ok" / "failed"
  rows: int
  start_date: str | None
  end_date: str | None
  error: str | None

# -----------------------------
# Universe: current S&P 500
# -----------------------------
