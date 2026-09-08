from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _import_runtime_dependencies():
    try:
        import pandas as pd
        import pyomo.environ as pyo
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required package"
        raise SystemExit(
            f"Missing Python dependency: {missing}. Install with "
            "`pip install -r requirements.txt` and, for Gurobi users, "
            "`pip install -r requirements-gurobi.txt`."
        ) from exc
    return pd, pyo, plt


pd, pyo, plt = _import_runtime_dependencies()

from src.config.experiment_config import DEMO_CASE_STUDY_PATH  # noqa: E402
from src.data.demo_loader import load_seasonal_demo_data  # noqa: E402
from src.experiments.scenario_factory import build_scenario_payload, load_case_study_json  # noqa: E402
from src.optimization.extractors import extract_timeseries_and_kpis  # noqa: E402
from src.optimization.hybrid_builder import HybridModelInputs, build_hybrid_model  # noqa: E402
from src.optimization.solver import solve_hybrid_model  # noqa: E402


def _choose_solver(requested: str | None) -> str:
    candidates = [requested] if requested else ["highs", "appsi_highs", "gurobi", "cbc", "glpk"]
    for candidate in [c for c in candidates if c]:
        if pyo.SolverFactory(candidate).available(exception_flag=False):
            return candidate
    raise SystemExit(
        "No MILP solver is available to Pyomo. Install HiGHS (`highspy`) for the "
        "open-source demo path, or install/configure Gurobi."
    )


def _build_payload(case_study_path: Path):
    case_study_data = load_case_study_json(case_study_path)
    return build_scenario_payload(
        case_study_data=case_study_data,
        bess_capex_multiplier=1.0,
        h2_capex_multiplier=1.0,
        h2_performance_level="base",
        timestep_hours=1.0,
        grid_limit_multiplier=1.0,
    )


def _run_case(df, payload, solver_name: str, ssr_target: float | None, time_limit_s: int, mip_gap: float):
    run_mode = "unconstrained" if ssr_target is None else f"ssr_{int(ssr_target * 100)}"
    inputs = HybridModelInputs(
        study_id="demo_synthetic_seasonal_weeks",
        run_mode=run_mode,
        ssr_target=ssr_target,
        df=df,
        technical=payload.technical,
        economics=payload.economics,
        allow_grid_to_bess_charging=False,
    )
    model = build_hybrid_model(inputs)
    outcome = solve_hybrid_model(
        model=model,
        solver_name=solver_name,
        time_limit_s=time_limit_s,
        mip_gap=mip_gap,
        tee=False,
        study_id=inputs.study_id,
        run_mode=run_mode,
        ssr_target=ssr_target,
    )
    timeseries, kpis = extract_timeseries_and_kpis(model, df)
    row = {
        "study_id": inputs.study_id,
        "run_mode": run_mode,
        "ssr_target": ssr_target,
        "solver_name": solver_name,
        "solver_status": outcome.solver_status,
        "termination_condition": outcome.termination_condition,
        "solver_elapsed_s": outcome.elapsed_s,
        **asdict(kpis),
    }
    return row, timeseries


def _write_figure(summary_df, output_dir: Path) -> None:
    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, ax1 = plt.subplots(figsize=(6.5, 4.0))
    x = summary_df["run_mode"].astype(str)
    ax1.bar(x, summary_df["bess_capacity_kwh"], color="#4c78a8", label="BESS")
    ax1.set_ylabel("BESS capacity [kWh]")
    ax1.tick_params(axis="x", rotation=20)
    ax2 = ax1.twinx()
    ax2.plot(x, summary_df["tank_capacity_kg"], marker="s", color="#f58518", label="H2 tank")
    ax2.set_ylabel("H2 tank capacity [kg]")
    fig.tight_layout()
    fig.savefig(fig_dir / "demo_capacities.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the public synthetic seasonal-week MILP demo.")
    parser.add_argument("--solver", default=None, help="Pyomo solver name. Default: first available open-source/Gurobi solver.")
    parser.add_argument("--time-limit", type=int, default=300, help="Per-run solver time limit in seconds.")
    parser.add_argument("--mip-gap", type=float, default=0.01, help="Relative MIP gap for demo runs.")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data" / "demo" / "seasonal_weeks")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results" / "demo")
    parser.add_argument("--ssr-targets", nargs="*", type=float, default=[0.60, 0.70], help="Demo SSR targets, as fractions.")
    args = parser.parse_args()

    solver_name = _choose_solver(args.solver)
    df = load_seasonal_demo_data(args.data_dir)
    payload = _build_payload(DEMO_CASE_STUDY_PATH)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    capacity_rows = []
    for ssr_target in [None, *args.ssr_targets]:
        row, timeseries = _run_case(df, payload, solver_name, ssr_target, args.time_limit, args.mip_gap)
        rows.append(row)
        capacity_rows.append(
            {
                "run_mode": row["run_mode"],
                "ssr_target": row["ssr_target"],
                "achieved_ssr": row["achieved_ssr"],
                "bess_capacity_kwh": row["bess_capacity_kwh"],
                "electrolyzer_capacity_kw": row["electrolyzer_capacity_kw"],
                "fuel_cell_capacity_kw": row["fuel_cell_capacity_kw"],
                "tank_capacity_kg": row["tank_capacity_kg"],
            }
        )
        timeseries.to_csv(args.output_dir / f"{row['run_mode']}_timeseries.csv", index=True)

    summary_df = pd.DataFrame(rows)
    capacities_df = pd.DataFrame(capacity_rows)
    summary_df.to_csv(args.output_dir / "demo_summary.csv", index=False)
    capacities_df.to_csv(args.output_dir / "demo_capacities.csv", index=False)
    (args.output_dir / "demo_metadata.json").write_text(
        json.dumps(
            {
                "dataset": "synthetic seasonal weeks",
                "solver": solver_name,
                "rows": int(len(df)),
                "ssr_targets": args.ssr_targets,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_figure(capacities_df, args.output_dir)
    print(f"Demo complete. Wrote outputs under {args.output_dir}")


if __name__ == "__main__":
    main()
