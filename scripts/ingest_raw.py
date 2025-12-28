from src.data.ingest_stooq import ingest_sp500_raw_prices_stooq

if __name__ == "__main__":
  # Smoke test first; remove limit once stable
  results = ingest_sp500_raw_prices_stooq(limit=25)
  ok = sum(r.status == "ok" for r in results)
  failed = sum(r.status == "failed" for r in results)
  print(f"Done. ok={ok}, failed={failed}. See data_raw/manifest.csv")
