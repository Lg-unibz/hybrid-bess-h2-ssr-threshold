from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pyomo.environ as pyo


@dataclass(frozen=True)
class HybridRunKpis:
    """Annual KPIs and complete granular cost breakdown extracted directly from one solved MILP instance."""

    achieved_ssr: float
    tac_eur_per_year: float
    
    # Granular CAPEX Breakdown [EUR/year]
    annualized_capex_bess_eur: float
    annualized_capex_ely_eur: float
    annualized_capex_fc_eur: float
    annualized_capex_tank_eur: float
    annualized_capex_total_eur: float
    
    # Granular Fixed OPEX Breakdown [EUR/year]
    opex_fixed_bess_eur: float
    opex_fixed_ely_eur: float
    opex_fixed_fc_eur: float
    opex_fixed_tank_eur: float
    opex_fixed_total_eur: float
    
    # Granular Variable OPEX Breakdown [EUR/year]
    opex_variable_bess_eur: float
    opex_variable_ely_eur: float
    opex_variable_fc_eur: float
    opex_variable_tank_eur: float
    opex_variable_total_eur: float
    
    # Grid Exchange Breakdown [EUR/year]
    grid_import_cost_eur: float
    grid_export_revenue_eur: float
    grid_net_cost_eur: float
    
    # Installed Design Capacities
    bess_capacity_kwh: float
    electrolyzer_capacity_kw: float
    fuel_cell_capacity_kw: float
    tank_capacity_kg: float
    
    # Energy Volumes [kWh or kg]
    annual_grid_import_kwh: float
    annual_grid_export_kwh: float
    annual_pv_curtailed_kwh: float
    annual_pv_curtailed_share_of_available: float
    annual_h2_produced_kg: float
    annual_h2_used_kg: float
    
    # Component Status
    bess_installed: bool
    h2_installed: bool


def extract_timeseries_and_kpis(
    model: pyo.ConcreteModel, df_input: pd.DataFrame
) -> tuple[pd.DataFrame, HybridRunKpis]:
    """Extract hourly variables and annual KPIs with complete granular cost breakdown."""
    n = len(df_input)
    dt_h = float(pyo.value(model.dt_h))

    timeseries = df_input.copy()
    timeseries["p_bess_ch_kw"] = [float(pyo.value(model.p_bess_ch_kw[t])) for t in range(n)]
    timeseries["p_bess_dis_kw"] = [float(pyo.value(model.p_bess_dis_kw[t])) for t in range(n)]
    timeseries["bess_soc_kwh"] = [float(pyo.value(model.bess_soc_kwh[t])) for t in range(n)]
    timeseries["p_pv_used_kw"] = [float(pyo.value(model.p_pv_used_kw[t])) for t in range(n)]
    timeseries["p_pv_curtailed_kw"] = [float(pyo.value(model.p_pv_curtailed_kw[t])) for t in range(n)]
    timeseries["p_grid_buy_kw"] = [float(pyo.value(model.p_grid_buy_kw[t])) for t in range(n)]
    timeseries["p_grid_sell_kw"] = [float(pyo.value(model.p_grid_sell_kw[t])) for t in range(n)]
    timeseries["p_ely_kw"] = [float(pyo.value(model.p_ely_kw[t])) for t in range(n)]
    timeseries["p_fc_kw"] = [float(pyo.value(model.p_fc_kw[t])) for t in range(n)]
    timeseries["tank_mass_kg"] = [float(pyo.value(model.tank_mass_kg[t])) for t in range(n)]

    # Sub-flows
    if hasattr(model, "p_pv_to_load_kw"):
        timeseries["p_pv_to_load_kw"] = [float(pyo.value(model.p_pv_to_load_kw[t])) for t in range(n)]
        timeseries["p_pv_to_bess_kw"] = [float(pyo.value(model.p_pv_to_bess_kw[t])) for t in range(n)]
        timeseries["p_pv_to_ely_kw"] = [float(pyo.value(model.p_pv_to_ely_kw[t])) for t in range(n)]
        timeseries["p_pv_to_grid_kw"] = [float(pyo.value(model.p_pv_to_grid_kw[t])) for t in range(n)]
        timeseries["p_grid_to_load_kw"] = [float(pyo.value(model.p_grid_to_load_kw[t])) for t in range(n)]
        timeseries["p_grid_to_bess_kw"] = [float(pyo.value(model.p_grid_to_bess_kw[t])) for t in range(n)]

    timeseries["bess_charged_kwh"] = timeseries["p_bess_ch_kw"] * dt_h
    timeseries["bess_discharged_kwh"] = timeseries["p_bess_dis_kw"] * dt_h
    timeseries["pv_used_kwh"] = timeseries["p_pv_used_kw"] * dt_h
    timeseries["pv_curtailed_kwh"] = timeseries["p_pv_curtailed_kw"] * dt_h
    timeseries["grid_import_kwh"] = timeseries["p_grid_buy_kw"] * dt_h
    timeseries["grid_export_kwh"] = timeseries["p_grid_sell_kw"] * dt_h

    eta_ely = float(pyo.value(model.eta_ely))
    eta_fc = float(pyo.value(model.eta_fc))
    lhv_kwh_per_kg = float(pyo.value(model.h2_lhv_kwh_per_kg))

    timeseries["h2_produced_kg"] = (timeseries["p_ely_kw"] * eta_ely / lhv_kwh_per_kg) * dt_h
    timeseries["h2_used_kg"] = (timeseries["p_fc_kw"] / (eta_fc * lhv_kwh_per_kg)) * dt_h

    annual_grid_import_kwh = float(timeseries["grid_import_kwh"].sum())
    annual_grid_export_kwh = float(timeseries["grid_export_kwh"].sum())
    annual_pv_curtailed_kwh = float(timeseries["pv_curtailed_kwh"].sum())
    annual_pv_available_kwh = float(timeseries["pv_production_kwh"].sum())
    annual_demand_kwh = float(timeseries["demand_kwh"].sum())

    # Grid Exchange Breakdown
    grid_import_cost_eur = float((timeseries["grid_import_kwh"] * timeseries["price_buy_eur_kwh"]).sum())
    grid_export_revenue_eur = float((timeseries["grid_export_kwh"] * timeseries["price_sell_eur_kwh"]).sum())
    grid_net_cost_eur = grid_import_cost_eur - grid_export_revenue_eur

    # Capacities
    bess_capacity_kwh = float(pyo.value(model.bess_add_kwh))
    ely_capacity_kw = float(pyo.value(model.ely_capacity_kw))
    fc_capacity_kw = float(pyo.value(model.fc_capacity_kw))
    tank_capacity_kg = float(pyo.value(model.tank_capacity_kg))

    # Annualized CAPEX Breakdown
    annualized_capex_bess_eur = float(bess_capacity_kwh * pyo.value(model.bess_ann_eur_per_kwh_year))
    annualized_capex_ely_eur = float(ely_capacity_kw * pyo.value(model.ely_ann_eur_per_kw_year))
    annualized_capex_fc_eur = float(fc_capacity_kw * pyo.value(model.fc_ann_eur_per_kw_year))
    annualized_capex_tank_eur = float(tank_capacity_kg * pyo.value(model.tank_ann_eur_per_kg_year))
    annualized_capex_total_eur = (
        annualized_capex_bess_eur
        + annualized_capex_ely_eur
        + annualized_capex_fc_eur
        + annualized_capex_tank_eur
    )

    # Fixed OPEX Breakdown
    opex_fixed_bess_eur = float(bess_capacity_kwh * pyo.value(model.bess_opex_fixed_eur_per_kwh_year))
    opex_fixed_ely_eur = float(ely_capacity_kw * pyo.value(model.ely_opex_fixed_eur_per_kw_year))
    opex_fixed_fc_eur = float(fc_capacity_kw * pyo.value(model.fc_opex_fixed_eur_per_kw_year))
    opex_fixed_tank_eur = float(tank_capacity_kg * pyo.value(model.tank_opex_fixed_eur_per_kg_year))
    opex_fixed_total_eur = (
        opex_fixed_bess_eur
        + opex_fixed_ely_eur
        + opex_fixed_fc_eur
        + opex_fixed_tank_eur
    )

    # Variable OPEX Breakdown
    opex_variable_bess_eur = float(
        pyo.value(model.bess_opex_variable_eur_per_kwh_throughput)
        * (timeseries["bess_charged_kwh"] + timeseries["bess_discharged_kwh"]).sum()
    )
    opex_variable_ely_eur = float(
        pyo.value(model.ely_opex_variable_eur_per_kwh_input) * (timeseries["p_ely_kw"] * dt_h).sum()
    )
    opex_variable_fc_eur = float(
        pyo.value(model.fc_opex_variable_eur_per_kwh_output) * (timeseries["p_fc_kw"] * dt_h).sum()
    )
    opex_variable_tank_eur = float(
        pyo.value(model.tank_opex_variable_eur_per_kg_throughput)
        * (timeseries["h2_produced_kg"] + timeseries["h2_used_kg"]).sum()
    )
    opex_variable_total_eur = (
        opex_variable_bess_eur
        + opex_variable_ely_eur
        + opex_variable_fc_eur
        + opex_variable_tank_eur
    )

    # Exact TAC from model objective
    tac_eur = float(pyo.value(model.objective))

    annual_h2_produced = float(timeseries["h2_produced_kg"].sum())
    annual_h2_used = float(timeseries["h2_used_kg"].sum())

    bess_installed = bess_capacity_kwh > 1e-4
    # A usable H2 chain requires all three sizing decisions.  The tolerance is
    # only a numerical-zero check, not a scientific adoption threshold.
    h2_installed = (
        (ely_capacity_kw > 1e-4)
        and (fc_capacity_kw > 1e-4)
        and (tank_capacity_kg > 1e-4)
    )

    kpis = HybridRunKpis(
        achieved_ssr=(1.0 - annual_grid_import_kwh / annual_demand_kwh) if annual_demand_kwh > 0 else 0.0,
        tac_eur_per_year=tac_eur,
        annualized_capex_bess_eur=annualized_capex_bess_eur,
        annualized_capex_ely_eur=annualized_capex_ely_eur,
        annualized_capex_fc_eur=annualized_capex_fc_eur,
        annualized_capex_tank_eur=annualized_capex_tank_eur,
        annualized_capex_total_eur=annualized_capex_total_eur,
        opex_fixed_bess_eur=opex_fixed_bess_eur,
        opex_fixed_ely_eur=opex_fixed_ely_eur,
        opex_fixed_fc_eur=opex_fixed_fc_eur,
        opex_fixed_tank_eur=opex_fixed_tank_eur,
        opex_fixed_total_eur=opex_fixed_total_eur,
        opex_variable_bess_eur=opex_variable_bess_eur,
        opex_variable_ely_eur=opex_variable_ely_eur,
        opex_variable_fc_eur=opex_variable_fc_eur,
        opex_variable_tank_eur=opex_variable_tank_eur,
        opex_variable_total_eur=opex_variable_total_eur,
        grid_import_cost_eur=grid_import_cost_eur,
        grid_export_revenue_eur=grid_export_revenue_eur,
        grid_net_cost_eur=grid_net_cost_eur,
        bess_capacity_kwh=bess_capacity_kwh,
        electrolyzer_capacity_kw=ely_capacity_kw,
        fuel_cell_capacity_kw=fc_capacity_kw,
        tank_capacity_kg=tank_capacity_kg,
        annual_grid_import_kwh=annual_grid_import_kwh,
        annual_grid_export_kwh=annual_grid_export_kwh,
        annual_pv_curtailed_kwh=annual_pv_curtailed_kwh,
        annual_pv_curtailed_share_of_available=(
            annual_pv_curtailed_kwh / annual_pv_available_kwh
            if annual_pv_available_kwh > 0.0
            else 0.0
        ),
        annual_h2_produced_kg=annual_h2_produced,
        annual_h2_used_kg=annual_h2_used,
        bess_installed=bess_installed,
        h2_installed=h2_installed,
    )

    return timeseries, kpis
