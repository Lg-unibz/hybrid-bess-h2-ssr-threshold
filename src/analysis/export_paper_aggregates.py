from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


COARSE_TARGETS = [0.70, 0.80, 0.90, 1.00]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "skipped" in out:
        out = out[out["skipped"].astype(str).str.lower().isin(["false", "0", "0.0", "nan", "none", ""])]
    if "run_status" in out:
        mask = out["run_status"].astype(str).str.contains("Completed|nan|None", case=False, na=True)
        out = out[mask]
    if "solver_status" in out:
        out = out[out["solver_status"].astype(str).str.lower().isin(["ok", "optimal", "warning"])]
    if "termination_condition" in out:
        out = out[out["termination_condition"].astype(str).str.lower().isin(["optimal", "feasible", "maxtimelimit"])]
    out["achieved_ssr"] = pd.to_numeric(out["achieved_ssr"], errors="coerce")
    out["ssr_target"] = pd.to_numeric(out["ssr_target"], errors="coerce")
    out["ssr_target_rounded"] = out["ssr_target"].round(2)
    return out.dropna(subset=["achieved_ssr"])


def _h2_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (scenario, weather_year), group in df.groupby(["factor_level", "weather_year"], dropna=False):
        h2 = group[group["h2_installed"].astype(str).str.lower().isin(["true", "1", "1.0"])]
        if h2.empty:
            rows.append({"factor_level": scenario, "weather_year": weather_year, "h2_threshold_ssr_pct": None})
        else:
            row = h2.loc[h2["achieved_ssr"].idxmin()]
            rows.append(
                {
                    "factor_level": scenario,
                    "weather_year": weather_year,
                    "h2_threshold_ssr_pct": float(row["achieved_ssr"]) * 100.0,
                    "bess_capacity_kwh": row.get("bess_capacity_kwh"),
                    "electrolyzer_capacity_kw": row.get("electrolyzer_capacity_kw"),
                    "fuel_cell_capacity_kw": row.get("fuel_cell_capacity_kw"),
                    "tank_capacity_kg": row.get("tank_capacity_kg"),
                }
            )
    return pd.DataFrame(rows)


def _median_weather_year(df: pd.DataFrame) -> object:
    if "weather_role" in df:
        median_rows = df[df["weather_role"].astype(str).str.lower() == "median"]
        if not median_rows.empty:
            return median_rows["weather_year"].iloc[0]
    return sorted(df["weather_year"].dropna().unique())[0]


def _baseline_absolute(df: pd.DataFrame, median_year: object) -> pd.DataFrame:
    base = df[(df["factor_level"] == "OFAT-Baseline") & (df["weather_year"] == median_year)]
    base = base[base["ssr_target_rounded"].isin(COARSE_TARGETS)]
    cols = [
        "ssr_target_rounded",
        "tac_eur_per_year",
        "bess_capacity_kwh",
        "electrolyzer_capacity_kw",
        "fuel_cell_capacity_kw",
        "tank_capacity_kg",
        "annual_h2_used_kg",
    ]
    return base[cols].sort_values("ssr_target_rounded")


def _tac_shift(df: pd.DataFrame, median_year: object) -> tuple[pd.DataFrame, pd.DataFrame]:
    coarse = df[df["ssr_target_rounded"].isin(COARSE_TARGETS)].copy()
    base = coarse[coarse["factor_level"] == "OFAT-Baseline"][
        ["weather_year", "ssr_target_rounded", "tac_eur_per_year"]
    ].rename(columns={"tac_eur_per_year": "baseline_tac_eur_per_year"})
    merged = coarse.merge(base, on=["weather_year", "ssr_target_rounded"], how="left")
    merged["tac_shift_k_eur_per_year"] = (
        pd.to_numeric(merged["tac_eur_per_year"], errors="coerce")
        - pd.to_numeric(merged["baseline_tac_eur_per_year"], errors="coerce")
    ) / 1000.0
    median = merged[merged["weather_year"] == median_year]
    weather_ranges = (
        merged.groupby(["factor_level", "ssr_target_rounded"], as_index=False)
        .agg(
            tac_shift_min_k_eur_per_year=("tac_shift_k_eur_per_year", "min"),
            tac_shift_max_k_eur_per_year=("tac_shift_k_eur_per_year", "max"),
        )
    )
    return median, weather_ranges


def _component_substitution(df: pd.DataFrame, median_year: object, target: float) -> pd.DataFrame:
    subset = df[(df["weather_year"] == median_year) & (df["ssr_target_rounded"] == round(target, 2))].copy()
    base = subset[subset["factor_level"] == "OFAT-Baseline"]
    if base.empty:
        return pd.DataFrame()
    metrics = [
        "bess_capacity_kwh",
        "electrolyzer_capacity_kw",
        "fuel_cell_capacity_kw",
        "tank_capacity_kg",
        "annual_h2_used_kg",
    ]
    base_values = base.iloc[0]
    rows = []
    for _, row in subset.iterrows():
        out = {"factor_level": row["factor_level"], "ssr_target": target, "weather_year": median_year}
        for metric in metrics:
            denom = float(base_values.get(metric, 0.0) or 0.0)
            value = float(row.get(metric, 0.0) or 0.0)
            out[f"{metric}_pct_vs_baseline"] = None if denom == 0.0 else 100.0 * (value - denom) / denom
        rows.append(out)
    return pd.DataFrame(rows)


def export_aggregates(run_summary: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df = _clean(pd.read_csv(run_summary))
    median_year = _median_weather_year(df)
    _baseline_absolute(df, median_year).to_csv(output_dir / "baseline_absolute_values_median_year.csv", index=False)
    _h2_thresholds(df).to_csv(output_dir / "h2_thresholds_by_scenario_weather.csv", index=False)
    median_shift, weather_ranges = _tac_shift(df, median_year)
    median_shift.to_csv(output_dir / "tac_shift_median_year.csv", index=False)
    weather_ranges.to_csv(output_dir / "tac_shift_weather_ranges.csv", index=False)
    for target in [0.80, 0.90, 1.00]:
        _component_substitution(df, median_year, target).to_csv(
            output_dir / f"component_substitution_{int(target * 100)}_ssr_median_year.csv",
            index=False,
        )
    worst = df[df["factor_level"].astype(str).str.contains("WorstCase", case=False, na=False)]
    worst.to_csv(output_dir / "worst_case_feasibility_summary.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export non-confidential aggregate CSVs from a private run_summary file.")
    parser.add_argument("run_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("results/paper_aggregated"))
    args = parser.parse_args()
    export_aggregates(args.run_summary, args.output_dir)


if __name__ == "__main__":
    main()

