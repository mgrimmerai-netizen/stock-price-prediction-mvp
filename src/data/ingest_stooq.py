from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import enum
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

# -----------------------------
# Config / constants
# -----------------------------
STOOQ_BASE = "https://stooq.com/q/d/l"
RAW_DIR = Path("/content/repo/data_raw")
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
  tables = pd.read_html(StringIO(response.text))
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

# -----------------------------
# Download: Stooq daily data
# -----------------------------

def download_stooq_daily_csv(stooq_symbol: str, timeout: int = 30) -> pd.DataFrame:
  """
  Downloads daily data from Stooq. Returns DataFrame with columns:
  date, open, high, low, close, volume
  """
  params = {"s": stooq_symbol.lower(), "i": "d"} # stooq expects lowercase symbol
  r = requests.get(STOOQ_BASE, params=params, timeout=timeout)
  r.raise_for_status()

  # Stooq return CSV text; parse via pandas
  df = pd.read_csv(StringIO(r.text))

  if df.empty or "Date" not in df.columns:
    raise ValueError("Empty or unexpected CSV format from Stooq.")
  
  # Canonicalize column names for raw layer readability
  df = df.rename(columns={
    "Date": "date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
  })

  # Normalize date type and ordering
  df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
  df =  df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

  return df

# -----------------------------
# Persistence: raw files + manifest
# -----------------------------

def ensure_dirs() -> None:
    PRICES_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def save_raw_ticker_csv(ticker: str, df: pd.DataFrame) -> Path:
    """
    Saves raw data for a ticker as CSV in data/raw/prices/{TICKER}.csv
    """
    out_path = PRICES_DIR / f"{ticker.upper()}.csv"
    df.to_csv(out_path, index=False)
    return out_path

def append_manifest_row(row: dict) -> None:
    """
    Appends a single row to data/raw/manifest.csv (creates if absent).
    """
    ensure_dirs()
    manifest_df = pd.DataFrame([row])
    if MANIFEST_PATH.exists():
        manifest_df.to_csv(MANIFEST_PATH, mode="a", header=False, index=False)
    else:
        manifest_df.to_csv(MANIFEST_PATH, mode="w", header=True, index=False)


def ingest_sp500_raw_prices_stooq(
  limit: int | None,
  pause_every: int = 50,
) -> list[DownloadResult]:
  """
  Main entrypoint: downloads raw daily price data for current S&P500 tickers.
  Writes per-ticker CSV files and a manifest log.
  """
  ensure_dirs()

  tickers = get_sp500_tickers_from_wikipedia()
  if limit is not None:
    tickers = tickers[:limit]
  
  results: list[DownloadResult] = []
  ts = datetime.now(timezone.utc).isoformat()

  for idx, ticker in enumerate(tickers, start=1):
    stooq_symbol = normalize_ticker_for_stooq(ticker)

    try:
      df = download_stooq_daily_csv(stooq_symbol)

      # Minimal sanity: need at least some data
      if len(df) < 10:
        raise ValueError(f"Too few rows ({len(df)}) returned.")
      
      save_raw_ticker_csv(ticker, df)

      start_date = str(df["date"].iloc[0])
      end_date = str(df["date"].iloc[-1])

      res = DownloadResult(
        ticker=ticker,
        stooq_symbol=stooq_symbol,
        status="ok",
        rows=len(df),
        start_date=start_date,
        end_date=end_date,
        error=None,
      )

    except Exception as e:
      res = DownloadResult(
        ticker=ticker,
        stooq_symbol=stooq_symbol,
        status="failed",
        rows=0,
        start_date=None,
        end_date=None,
        error=str(e),
      )
    
    results.append(res)

    # Write manifest entry for every ticker (including failures)
    append_manifest_row({
      "download_timestamp_utc": ts,
      "source": "stooq",
      "ticker": res.ticker,
      "status": res.status,
      "rows": res.rows,
      "start_date": res.start_date,
      "end_date": res.end_date,
      "error": res.error,
    })

    # Optional: a lightweight pause hook if you later add rate limiting
    if pause_every and idx % pause_every == 0:
      pass
  
  return results



if __name__ == "__main__":
    # MVP smoke test: limit to a small subset first
    ingest_sp500_raw_prices_stooq(limit=10)



