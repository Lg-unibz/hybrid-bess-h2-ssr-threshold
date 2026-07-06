from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "demo" / "seasonal_weeks"

SEASONS = {
    "winter": {"start": "2019-01-07T00:00:00", "daylight": 8.5, "pv_peak": 20.0, "base": 5.6},
    "spring": {"start": "2019-04-08T00:00:00", "daylight": 12.8, "pv_peak": 38.0, "base": 5.2},
    "summer": {"start": "2019-07-08T00:00:00", "daylight": 15.2, "pv_peak": 48.0, "base": 6.1},
    "autumn": {"start": "2019-10-07T00:00:00", "daylight": 10.7, "pv_peak": 28.0, "base": 5.8},
}


def _pv_profile(hour: int, daylight: float, peak: float, cloud_factor: float) -> float:
    sunrise = 12.0 - daylight / 2.0
    sunset = 12.0 + daylight / 2.0
    if hour < sunrise or hour > sunset:
        return 0.0
    x = (hour - sunrise) / max(daylight, 1e-9)
    return max(0.0, peak * math.sin(math.pi * x) ** 1.55 * cloud_factor)


def _demand_profile(hour: int, weekday: int, base: float, season: str) -> float:
    morning = 2.8 * math.exp(-((hour - 7.0) / 2.4) ** 2)
    working = 4.8 if 8 <= hour <= 18 and weekday < 6 else 2.4
    evening = 1.4 * math.exp(-((hour - 20.0) / 2.8) ** 2)
    cooling = 1.3 if season == "summer" and 11 <= hour <= 17 else 0.0
    winter_aux = 0.8 if season == "winter" and (hour <= 6 or hour >= 18) else 0.0
    deterministic_variation = 0.35 * math.sin((weekday + 1) * 1.7 + hour / 3.0)
    return max(0.5, base + morning + working + evening + cooling + winter_aux + deterministic_variation)


def build_rows(season: str, spec: dict[str, float | str]) -> list[dict[str, object]]:
    start = datetime.fromisoformat(str(spec["start"]))
    rows: list[dict[str, object]] = []
    for step in range(7 * 24):
        ts = start + timedelta(hours=step)
        weekday = ts.weekday()
        cloud_factor = 0.78 + 0.18 * math.sin((weekday + 1) * 1.13) + 0.06 * math.cos(ts.hour / 2.5)
        cloud_factor = max(0.55, min(1.02, cloud_factor))
        demand = _demand_profile(ts.hour, weekday, float(spec["base"]), season)
        pv = _pv_profile(ts.hour, float(spec["daylight"]), float(spec["pv_peak"]), cloud_factor)
        buy_price = 0.18 + (0.04 if 8 <= ts.hour <= 20 else 0.0) + (0.015 if season == "winter" else 0.0)
        sell_price = buy_price / 2.0
        rows.append(
            {
                "timestamp": ts.isoformat(sep=" "),
                "season": season,
                "demand_kwh": round(demand, 4),
                "pv_production_kwh": round(pv, 4),
                "price_buy_eur_kwh": round(buy_price, 4),
                "price_sell_eur_kwh": round(sell_price, 4),
            }
        )
    return rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp",
        "season",
        "demand_kwh",
        "pv_production_kwh",
        "price_buy_eur_kwh",
        "price_sell_eur_kwh",
    ]
    for season, spec in SEASONS.items():
        rows = build_rows(season, spec)
        with (OUTPUT_DIR / f"{season}_week.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()

