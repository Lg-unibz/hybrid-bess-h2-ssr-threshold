from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_INPUTS = [
    "input/processed/electricity_demand/csv/2024_h.csv",
    "input/processed/pv_production/csv/production_global_2007.csv",
    "input/processed/pv_production/csv/production_global_2014.csv",
    "input/processed/pv_production/csv/production_global_2018.csv",
    "input/processed/prices/csv/pun_2020.csv",
    "input/processed/prices/csv/pun_2022.csv",
    "input/processed/prices/csv/pun_2024.csv",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight helper for paper-scale reruns. The full campaign requires "
            "the confidential full-year demand profile and is not executable from "
            "the public repository alone."
        )
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Repository root containing the input/ folder.")
    args = parser.parse_args()

    print("Full paper-scale execution requires confidential full-year demand data and a private HPC workflow.")
    print("Expected input paths are relative to the repository root:")
    for rel in REQUIRED_INPUTS:
        print(f"  - {rel}")

    missing = [rel for rel in REQUIRED_INPUTS if not (args.root / rel).exists()]
    if missing:
        print("\nPaper-scale rerun inputs are incomplete. Missing:")
        for rel in missing:
            print(f"  - {rel}")
        print("\nSee DATA_AVAILABILITY.md and REPRODUCIBILITY.md for the reproducibility levels.")
        return

    print("\nAll expected paper-scale input placeholders are present.")
    print("Use the private workflow or adapt scripts/run_demo.py with the full-year loader and campaign configuration.")


if __name__ == "__main__":
    main()

