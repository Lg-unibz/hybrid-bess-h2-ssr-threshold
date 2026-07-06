from __future__ import annotations


def compute_crf(real_discount_rate: float, lifetime_years: int) -> float:
    """Compute the capital recovery factor used for annualized CAPEX."""
    if lifetime_years <= 0:
        raise ValueError("lifetime_years must be positive")
    if real_discount_rate <= 0:
        return 1.0 / float(lifetime_years)

    r = float(real_discount_rate)
    n = float(lifetime_years)
    return r * (1.0 + r) ** n / ((1.0 + r) ** n - 1.0)


def compute_discounted_replacement_cost(
    initial_capex_eur_per_unit: float,
    replacement_fraction_of_initial_capex: float,
    component_lifetime_years: int,
    project_lifetime_years: int,
    real_discount_rate: float,
) -> float:
    """Discount replacement costs to present value.

    Replacement years are t in [L_comp, 2*L_comp, ...] strictly lower than
    L_proj. Each replacement cost is C_rep = replacement_fraction * I_0.
    """
    if component_lifetime_years <= 0:
        raise ValueError("component_lifetime_years must be positive")
    if project_lifetime_years <= 0:
        raise ValueError("project_lifetime_years must be positive")
    if replacement_fraction_of_initial_capex < 0.0:
        raise ValueError("replacement_fraction_of_initial_capex must be >= 0")
    if real_discount_rate <= -1.0:
        raise ValueError("real_discount_rate must be greater than -1")

    if component_lifetime_years >= project_lifetime_years:
        return 0.0

    replacement_cost_eur_per_unit = (
        replacement_fraction_of_initial_capex * initial_capex_eur_per_unit
    )
    if replacement_cost_eur_per_unit == 0.0:
        return 0.0

    r = float(real_discount_rate)
    pv_replacements_eur_per_unit = 0.0
    for year in range(component_lifetime_years, project_lifetime_years, component_lifetime_years):
        pv_replacements_eur_per_unit += replacement_cost_eur_per_unit / (1.0 + r) ** float(year)
    return pv_replacements_eur_per_unit


def compute_salvage_present_value(
    initial_capex_eur_per_unit: float,
    replacement_fraction_of_initial_capex: float,
    component_lifetime_years: int,
    project_lifetime_years: int,
    real_discount_rate: float,
) -> float:
    """Compute discounted salvage value with linear depreciation.

    Salvage is applied only to components with lifespan shorter than project
    lifetime. Following the contract:
    L_rem = L_comp - (L_proj mod L_comp) if mod != 0 else 0
    V_salvage = C_rep * (L_rem / L_comp)
    PV_salvage = V_salvage / (1 + r)^L_proj
    """
    if component_lifetime_years <= 0:
        raise ValueError("component_lifetime_years must be positive")
    if project_lifetime_years <= 0:
        raise ValueError("project_lifetime_years must be positive")
    if replacement_fraction_of_initial_capex < 0.0:
        raise ValueError("replacement_fraction_of_initial_capex must be >= 0")
    if real_discount_rate <= -1.0:
        raise ValueError("real_discount_rate must be greater than -1")

    if component_lifetime_years >= project_lifetime_years:
        return 0.0

    project_mod_component = project_lifetime_years % component_lifetime_years
    if project_mod_component == 0:
        return 0.0

    replacement_cost_eur_per_unit = (
        replacement_fraction_of_initial_capex * initial_capex_eur_per_unit
    )
    remaining_lifetime_years = component_lifetime_years - project_mod_component
    salvage_value_eur_per_unit = (
        replacement_cost_eur_per_unit
        * float(remaining_lifetime_years)
        / float(component_lifetime_years)
    )

    r = float(real_discount_rate)
    return salvage_value_eur_per_unit / (1.0 + r) ** float(project_lifetime_years)


def compute_equivalent_investment_cost(
    initial_capex_eur_per_unit: float,
    replacement_fraction_of_initial_capex: float,
    component_lifetime_years: int,
    project_lifetime_years: int,
    real_discount_rate: float,
) -> float:
    """Compute equivalent investment cost I_eq = I_0 + PV_rep - PV_salvage."""
    pv_replacements_eur_per_unit = compute_discounted_replacement_cost(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=replacement_fraction_of_initial_capex,
        component_lifetime_years=component_lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    pv_salvage_eur_per_unit = compute_salvage_present_value(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=replacement_fraction_of_initial_capex,
        component_lifetime_years=component_lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    return (
        float(initial_capex_eur_per_unit)
        + pv_replacements_eur_per_unit
        - pv_salvage_eur_per_unit
    )


def compute_annualized_capex_from_equivalent_cost(
    initial_capex_eur_per_unit: float,
    replacement_fraction_of_initial_capex: float,
    component_lifetime_years: int,
    project_lifetime_years: int,
    real_discount_rate: float,
) -> float:
    """Annualize equivalent investment cost using project-level CRF."""
    equivalent_investment_cost_eur_per_unit = compute_equivalent_investment_cost(
        initial_capex_eur_per_unit=initial_capex_eur_per_unit,
        replacement_fraction_of_initial_capex=replacement_fraction_of_initial_capex,
        component_lifetime_years=component_lifetime_years,
        project_lifetime_years=project_lifetime_years,
        real_discount_rate=real_discount_rate,
    )
    project_crf = compute_crf(real_discount_rate, project_lifetime_years)
    return equivalent_investment_cost_eur_per_unit * project_crf


def max_grid_import_from_ssr(total_demand_kwh: float, ssr_target: float) -> float:
    """Convert SSR target to the equivalent annual upper bound on grid import."""
    if not 0.0 <= ssr_target <= 1.0:
        raise ValueError("ssr_target must be in [0, 1]")
    return (1.0 - ssr_target) * total_demand_kwh
