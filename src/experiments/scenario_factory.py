from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.config.experiment_config import H2_PERFORMANCE_MAP
from src.optimization.constraints import (
    compute_annualized_capex_from_equivalent_cost,
    compute_crf,
    compute_discounted_replacement_cost,
    compute_equivalent_investment_cost,
    compute_salvage_present_value,
)
from src.optimization.hybrid_builder import HybridEconomicInputs, HybridTechnicalInputs


@dataclass(frozen=True)
class ScenarioPayload:
    """Resolved assumptions for one study case before run-mode expansion."""

    technical: HybridTechnicalInputs
    economics: HybridEconomicInputs
    resolved_config: dict[str, Any]


@dataclass(frozen=True)
class ComponentFinancialContract:
    """Component-level financial assumptions from the TAC contract."""

    lifetime_years: int
    replacement_fraction_of_initial_capex: float
    fixed_opex_fraction_of_initial_capex: float


@dataclass(frozen=True)
class ComponentEconomicBreakdown:
    """Per-unit annualized CAPEX and fixed OPEX terms used by the model."""

    initial_capex_eur_per_unit: float
    component_lifetime_years: int
    replacement_fraction_of_initial_capex: float
    fixed_opex_fraction_of_initial_capex: float
    pv_replacements_eur_per_unit: float
    pv_salvage_eur_per_unit: float
    equivalent_investment_cost_eur_per_unit: float
    annualized_capex_eur_per_unit_year: float
    fixed_opex_eur_per_unit_year: float


DEFAULT_COMPONENT_FINANCIAL_CONTRACTS: dict[str, ComponentFinancialContract] = {
    "bess": ComponentFinancialContract(
        lifetime_years=10,
        replacement_fraction_of_initial_capex=0.80,
        fixed_opex_fraction_of_initial_capex=0.025,
    ),
    "ely": ComponentFinancialContract(
        lifetime_years=10,
        replacement_fraction_of_initial_capex=0.40,
        fixed_opex_fraction_of_initial_capex=0.0275,
    ),
    "fc": ComponentFinancialContract(
        lifetime_years=10,
        replacement_fraction_of_initial_capex=0.40,
        fixed_opex_fraction_of_initial_capex=0.0275,
    ),
    "tank": ComponentFinancialContract(
        lifetime_years=20,
        replacement_fraction_of_initial_capex=0.00,
        fixed_opex_fraction_of_initial_capex=0.010,
    ),
    "pv": ComponentFinancialContract(
        lifetime_years=20,
        replacement_fraction_of_initial_capex=0.00,
        fixed_opex_fraction_of_initial_capex=0.025,
    ),
    "wind": ComponentFinancialContract(
        lifetime_years=20,
        replacement_fraction_of_initial_capex=0.00,
        fixed_opex_fraction_of_initial_capex=0.025,
    ),
}


def load_case_study_json(path: Path) -> dict[str, Any]:
    """Load base case-study assumptions from JSON."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_component_financial_contract(
    component_cfg: dict[str, Any],
    defaults: ComponentFinancialContract,
) -> ComponentFinancialContract:
    """Resolve financial assumptions with optional per-component overrides.

    Overrides are read from component_cfg["economics"] when present.
    """
    economics_cfg = component_cfg.get("economics", {})
    if not isinstance(economics_cfg, dict):
        economics_cfg = {}

    return ComponentFinancialContract(
        lifetime_years=int(economics_cfg.get("lifetime_years", defaults.lifetime_years)),
        replacement_fraction_of_initial_capex=float(
            economics_cfg.get(
                "replacement_fraction_of_initial_capex",
                defaults.replacement_fraction_of_initial_capex,
            )
        ),
        fixed_opex_fraction_of_initial_capex=float(
            economics_cfg.get(
                "fixed_opex_fraction_of_initial_capex",
                defaults.fixed_opex_fraction_of_initial_capex,
            )
        ),
    )


def _build_component_economic_breakdown(
    initial_capex_eur_per_unit: float,
    contract: ComponentFinancialContract,
    project_lifetime_years: int,
    real_discount_rate: float,
) -> ComponentEconomicBreakdown:
    """Build annualized CAPEX and fixed OPEX per-unit coefficients."""
    pv_replacements = compute_discounted_replacement_cost(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=contract.replacement_fraction_of_initial_capex,
        component_lifetime_years=contract.lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    pv_salvage = compute_salvage_present_value(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=contract.replacement_fraction_of_initial_capex,
        component_lifetime_years=contract.lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    equivalent_investment_cost = compute_equivalent_investment_cost(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=contract.replacement_fraction_of_initial_capex,
        component_lifetime_years=contract.lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    annualized_capex = compute_annualized_capex_from_equivalent_cost(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=contract.replacement_fraction_of_initial_capex,
        component_lifetime_years=contract.lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    fixed_opex = contract.fixed_opex_fraction_of_initial_capex * initial_capex_eur_per_unit

    return ComponentEconomicBreakdown(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        component_lifetime_years=contract.lifetime_years,
        replacement_fraction_of_initial_capex=contract.replacement_fraction_of_initial_capex,
        fixed_opex_fraction_of_initial_capex=contract.fixed_opex_fraction_of_initial_capex,
        pv_replacements_eur_per_unit=pv_replacements,
        pv_salvage_eur_per_unit=pv_salvage,
        equivalent_investment_cost_eur_per_unit=equivalent_investment_cost,
        annualized_capex_eur_per_unit_year=annualized_capex,
        fixed_opex_eur_per_unit_year=fixed_opex,
    )


def build_scenario_payload(
    case_study_data: dict[str, Any],
    bess_capex_multiplier: float,
    h2_capex_multiplier: float,
    h2_performance_level: str,
    timestep_hours: float,
    *,
    bess_capex_eur_kwh_override: float | None = None,
    ely_capex_eur_kw_override: float | None = None,
    fc_capex_eur_kw_override: float | None = None,
    tank_capex_eur_kg_override: float | None = None,
    eta_ely_override: float | None = None,
    eta_fc_override: float | None = None,
    bess_roundtrip_efficiency_override: float | None = None,
    grid_limit_multiplier: float = 1.0,
) -> ScenarioPayload:
    """Resolve one study case into model-ready technical and economic inputs."""
    storage = case_study_data["storage"]
    grid = case_study_data["grid"]
    finance = case_study_data["finance"]
    hydrogen = case_study_data["hydrogen"]

    perf = H2_PERFORMANCE_MAP[h2_performance_level]
    eta_ely = float(eta_ely_override) if eta_ely_override is not None else float(perf["eta_ely"])
    eta_fc = float(eta_fc_override) if eta_fc_override is not None else float(perf["eta_fc"])

    real_discount_rate = float(finance.get("real_discount_rate", 0.07))
    project_lifetime_years = int(finance.get("project_lifetime_years", 20))
    project_crf = compute_crf(real_discount_rate, project_lifetime_years)

    ely_cfg = hydrogen["electrolyzer"]
    fc_cfg = hydrogen["fuel_cell"]
    tank_cfg = hydrogen["tank"]

    bess_capex_initial_eur_per_kwh = (
        float(bess_capex_eur_kwh_override)
        if bess_capex_eur_kwh_override is not None
        else float(storage.get("capex_eur_kwh", 300.0)) * bess_capex_multiplier
    )
    ely_capex_initial_eur_per_kw = (
        float(ely_capex_eur_kw_override)
        if ely_capex_eur_kw_override is not None
        else float(ely_cfg["capex_eur_kw"]) * h2_capex_multiplier
    )
    fc_capex_initial_eur_per_kw = (
        float(fc_capex_eur_kw_override)
        if fc_capex_eur_kw_override is not None
        else float(fc_cfg["capex_eur_kw"]) * h2_capex_multiplier
    )
    tank_capex_initial_eur_per_kg = (
        float(tank_capex_eur_kg_override)
        if tank_capex_eur_kg_override is not None
        else float(tank_cfg["capex_eur_kg"]) * h2_capex_multiplier
    )

    if grid_limit_multiplier <= 0.0:
        raise ValueError("grid_limit_multiplier must be positive")

    bess_eta_roundtrip_fraction = (
        float(bess_roundtrip_efficiency_override)
        if bess_roundtrip_efficiency_override is not None
        else float(storage.get("roundtrip_efficiency_percent", 90.0)) / 100.0
    )

    bess_contract = _resolve_component_financial_contract(
        storage,
        DEFAULT_COMPONENT_FINANCIAL_CONTRACTS["bess"],
    )
    ely_contract = _resolve_component_financial_contract(
        ely_cfg,
        DEFAULT_COMPONENT_FINANCIAL_CONTRACTS["ely"],
    )
    fc_contract = _resolve_component_financial_contract(
        fc_cfg,
        DEFAULT_COMPONENT_FINANCIAL_CONTRACTS["fc"],
    )
    tank_contract = _resolve_component_financial_contract(
        tank_cfg,
        DEFAULT_COMPONENT_FINANCIAL_CONTRACTS["tank"],
    )

    bess_breakdown = _build_component_economic_breakdown(
        initial_capex_eur_per_unit=bess_capex_initial_eur_per_kwh,
        contract=bess_contract,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    ely_breakdown = _build_component_economic_breakdown(
        initial_capex_eur_per_unit=ely_capex_initial_eur_per_kw,
        contract=ely_contract,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    fc_breakdown = _build_component_economic_breakdown(
        initial_capex_eur_per_unit=fc_capex_initial_eur_per_kw,
        contract=fc_contract,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    tank_breakdown = _build_component_economic_breakdown(
        initial_capex_eur_per_unit=tank_capex_initial_eur_per_kg,
        contract=tank_contract,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )

    economics = HybridEconomicInputs(
        bess_annualized_eur_per_kwh_year=bess_breakdown.annualized_capex_eur_per_unit_year,
        ely_annualized_eur_per_kw_year=ely_breakdown.annualized_capex_eur_per_unit_year,
        fc_annualized_eur_per_kw_year=fc_breakdown.annualized_capex_eur_per_unit_year,
        tank_annualized_eur_per_kg_year=tank_breakdown.annualized_capex_eur_per_unit_year,
        bess_opex_fixed_eur_per_kwh_year=bess_breakdown.fixed_opex_eur_per_unit_year,
        ely_opex_fixed_eur_per_kw_year=ely_breakdown.fixed_opex_eur_per_unit_year,
        fc_opex_fixed_eur_per_kw_year=fc_breakdown.fixed_opex_eur_per_unit_year,
        tank_opex_fixed_eur_per_kg_year=tank_breakdown.fixed_opex_eur_per_unit_year,
        bess_opex_variable_eur_per_kwh_throughput=float(
            storage.get("opex_variable_eur_per_kwh_throughput", 0.0)
        ),
        ely_opex_variable_eur_per_kwh_input=float(
            ely_cfg.get("opex_variable_eur_per_kwh_input", 0.0)
        ),
        fc_opex_variable_eur_per_kwh_output=float(
            fc_cfg.get("opex_variable_eur_per_kwh_output", 0.0)
        ),
        tank_opex_variable_eur_per_kg_throughput=float(
            tank_cfg.get("opex_variable_eur_per_kg_throughput", 0.0)
        ),
    )

    technical = HybridTechnicalInputs(
        timestep_hours=timestep_hours,
        bess_eta_roundtrip=bess_eta_roundtrip_fraction,
        bess_soc_min_fraction=float(storage.get("soc_min_percent", 10.0)) / 100.0,
        bess_soc_max_fraction=float(storage.get("soc_max_percent", 90.0)) / 100.0,
        bess_self_discharge_fraction_per_hour=float(storage.get("self_discharge_percent_per_month", 3.0)) / 100.0 / (30.0 * 24.0),
        bess_default_c_rate_kw_per_kwh=float(storage.get("default_c_rate_kw_per_kwh", 0.5)),
        bess_capacity_upper_bound_kwh=float(storage.get("capacity_upper_bound_kwh", 10_000.0)),
        grid_max_import_kw=float(grid["max_import_kw"]) * grid_limit_multiplier,
        grid_max_export_kw=float(grid["max_export_kw"]) * grid_limit_multiplier,
        eta_ely=eta_ely,
        eta_fc=eta_fc,
        ely_min_load_fraction=float(ely_cfg.get("min_load_percent", 10.0)) / 100.0,
        ely_capacity_upper_bound_kw=float(ely_cfg["capacity_kw"]),
        fc_capacity_upper_bound_kw=float(fc_cfg["capacity_kw"]),
        tank_capacity_upper_bound_kg=float(tank_cfg["capacity_kg"]),
        tank_min_soc_fraction=float(tank_cfg.get("min_soc_percent", 5.0)) / 100.0,
    )

    resolved = {
        "bess_capex_multiplier": bess_capex_multiplier,
        "h2_capex_multiplier": h2_capex_multiplier,
        "h2_performance_level": h2_performance_level,
        "eta_ely": eta_ely,
        "eta_fc": eta_fc,
        "bess_eta_roundtrip": bess_eta_roundtrip_fraction,
        "grid_limit_multiplier": grid_limit_multiplier,
        "bess_capex_eur_kwh": bess_capex_initial_eur_per_kwh,
        "ely_capex_eur_kw": ely_capex_initial_eur_per_kw,
        "fc_capex_eur_kw": fc_capex_initial_eur_per_kw,
        "tank_capex_eur_kg": tank_capex_initial_eur_per_kg,
        "financial_mode": finance.get("financial_mode", "crf_real"),
        "real_discount_rate": real_discount_rate,
        "project_lifetime_years": project_lifetime_years,
        "project_crf": project_crf,
        "component_financial_contract": {
            name: asdict(contract)
            for name, contract in DEFAULT_COMPONENT_FINANCIAL_CONTRACTS.items()
        },
        "applied_financial_contract": {
            "bess": asdict(bess_contract),
            "electrolyzer": asdict(ely_contract),
            "fuel_cell": asdict(fc_contract),
            "tank": asdict(tank_contract),
        },
        "economic_breakdown_per_unit": {
            "bess": asdict(bess_breakdown),
            "electrolyzer": asdict(ely_breakdown),
            "fuel_cell": asdict(fc_breakdown),
            "tank": asdict(tank_breakdown),
        },
        "economics": {
            "bess_annualized_eur_per_kwh_year": economics.bess_annualized_eur_per_kwh_year,
            "ely_annualized_eur_per_kw_year": economics.ely_annualized_eur_per_kw_year,
            "fc_annualized_eur_per_kw_year": economics.fc_annualized_eur_per_kw_year,
            "tank_annualized_eur_per_kg_year": economics.tank_annualized_eur_per_kg_year,
            "bess_opex_fixed_eur_per_kwh_year": economics.bess_opex_fixed_eur_per_kwh_year,
            "ely_opex_fixed_eur_per_kw_year": economics.ely_opex_fixed_eur_per_kw_year,
            "fc_opex_fixed_eur_per_kw_year": economics.fc_opex_fixed_eur_per_kw_year,
            "tank_opex_fixed_eur_per_kg_year": economics.tank_opex_fixed_eur_per_kg_year,
            "bess_opex_variable_eur_per_kwh_throughput": economics.bess_opex_variable_eur_per_kwh_throughput,
            "ely_opex_variable_eur_per_kwh_input": economics.ely_opex_variable_eur_per_kwh_input,
            "fc_opex_variable_eur_per_kwh_output": economics.fc_opex_variable_eur_per_kwh_output,
            "tank_opex_variable_eur_per_kg_throughput": economics.tank_opex_variable_eur_per_kg_throughput,
        },
    }

    return ScenarioPayload(
        technical=technical,
        economics=economics,
        resolved_config=resolved,
    )
