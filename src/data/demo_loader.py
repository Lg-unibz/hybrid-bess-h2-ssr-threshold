from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "demand_kwh",
    "pv_production_kwh",
    "price_buy_eur_kwh",
    "price_sell_eur_kwh",
]


def load_seasonal_demo_data(data_dir: Path) -> pd.DataFrame:
    """Load and concatenate the four synthetic seasonal-week CSV files."""
    paths = [
        data_dir / "winter_week.csv",
        data_dir / "spring_week.csv",
        data_dir / "summer_week.csv",
        data_dir / "autumn_week.csv",
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing demo seasonal-week files: " + ", ".join(missing))

    frames: list[pd.DataFrame] = []
    for path in paths:
        df = pd.read_csv(path)
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{path} is missing columns: {missing_cols}")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("timestamp").drop_duplicates("timestamp", keep="first")
    out = out.set_index("timestamp")

    for col in REQUIRED_COLUMNS[1:]:
        out[col] = pd.to_numeric(out[col], errors="raise")

    return out

