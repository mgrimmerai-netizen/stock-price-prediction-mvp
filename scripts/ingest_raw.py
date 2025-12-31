import sys
from src.data.ingest_stooq import ingest_sp500_raw_prices_stooq

if __name__ == "__main__":
  results = ingest_sp500_raw_prices_stooq(limit=50)

  ok = sum(r.status == "ok" for r in results)
  failed = sum(r.status == "failed" for r in results)
  
  print(f"Done. ok={ok}, failed={failed}. See data_raw/manifest.csv")

  max_failure_rate = 0.05
  if len(results) > 0 and (failed / len(results)) > max_failure_rate:
    print(f"ERROR: failure_rate={(failed/len(results)):.2%} exceeds {max_failure_rate:.2%}")
    sys.exit(1)
