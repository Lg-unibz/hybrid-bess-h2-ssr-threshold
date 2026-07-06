from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = PROJECT_ROOT / "configs"
RESULTS_ROOT = PROJECT_ROOT / "results"
DEMO_RESULTS_ROOT = RESULTS_ROOT / "demo"

DEMO_CASE_STUDY_PATH = CONFIG_ROOT / "demo_case_study.json"
PAPER_SCENARIOS_PATH = CONFIG_ROOT / "paper_scenarios.json"

H2_PERFORMANCE_MAP: dict[str, dict[str, float]] = {
    "low": {"eta_ely": 0.55, "eta_fc": 0.45},
    "base": {"eta_ely": 0.65, "eta_fc": 0.50},
    "high": {"eta_ely": 0.75, "eta_fc": 0.60},
}

RUN_SUMMARY_COLUMNS: list[str] = [
    "study_id",
    "scenario_group",
    "scenario_description",
    "factor_name",
    "factor_level",
    "weather_variant",
    "weather_role",
    "weather_year",
    "pv_year",
    "pv_alignment_year",
    "pun_year",
    "price_multiplier",
    "bess_capex_multiplier",
    "h2_capex_multiplier",
    "bess_capex_eur_kwh",
    "bess_rte",
    "ely_capex_eur_kw",
    "fc_capex_eur_kw",
    "tank_capex_eur_kg",
    "grid_limit_multiplier",
    "eta_ely",
    "eta_fc",
    "run_mode",
    "ssr_target",
    "ssr_search_stage",
    "baseline_ssr_direct_pv",
    "run_status",
    "skipped",
    "skip_reason",
    "solver_status",
    "termination_condition",
    "achieved_ssr",
    "tac_eur_per_year",
    "opex_eur_per_year",
    "annualized_capex_bess_eur_per_year",
    "annualized_capex_h2_eur_per_year",
    "opex_fixed_bess_h2_eur_per_year",
    "bess_capacity_kwh",
    "electrolyzer_capacity_kw",
    "fuel_cell_capacity_kw",
    "tank_capacity_kg",
    "annual_grid_import_kwh",
    "annual_grid_export_kwh",
    "annual_pv_curtailed_kwh",
    "annual_pv_curtailed_share_of_available",
    "annual_h2_produced_kg",
    "annual_h2_used_kg",
    "bess_installed",
    "h2_installed",
]

