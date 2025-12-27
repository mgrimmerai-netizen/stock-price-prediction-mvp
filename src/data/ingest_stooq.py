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



@dataclass(frozen=True)
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

def get_sp500_tickers_from_wikipedia() -> list[str]:
  """Returns current S&P 500 tickers scraped from Wikipedia."""
  # fetch from Wikipedia
  url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
  headers = {
    "User-Agent": 
    "Mozilla/5.0 (compatible; research-script/1.0; +https://example.com)"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  tables = pd.read_html(response.text)
  # extract tickers
  sp500 = tables[0]
  tickers = sp500["Symbol"].astype(str).tolist()
  return tickers

def normalize_ticker_for_stooq(ticker: str) -> str:
  """
  Stooq uses dot suffix for exchange (US): e.g. AAPL.US
  and typically uses '-' instead of '.' in class shares (e.g., BRK-B.US).
  """
  t = ticker.strip().upper()
  t = t.replace(".", "-") # BRK.B -> BRK-B
  return f"{t}.US"






if __name__ == "__main__":
  tickers = get_sp500_tickers_from_wikipedia()
  for ticker in tickers:
    print(normalize_ticker_for_stooq(ticker))



