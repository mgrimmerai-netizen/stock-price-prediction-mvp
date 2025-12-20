from datetime import datetime
from pathlib import Path
import yaml


def main():
  create_report()

def create_report():
  # create timestamped report folder
  timestamp = datetime.now().strftime("%Y%d%m-%H%M%S")
  run_dir = Path("reports/runs") / timestamp
  run_dir.mkdir(parents=True)
  # save used configs
  cfg_path = Path("configs/experiment_v1.yaml")
  cfg = yaml.safe_load(cfg_path.read_text())
  cfg_out = run_dir / "config.yaml"
  cfg_out.write_text(yaml.dump(cfg))

if __name__=="__main__":
  main()