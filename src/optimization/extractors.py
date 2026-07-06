from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pyomo.environ as pyo


@dataclass(frozen=True)
class HybridRunKpis:
    """Annual KPIs extracted from one solved model instance."""

    achieved_ssr: float
    tac_eur_per_year: float
    opex_eur_per_year: float
    annualized_capex_bess_eur_per_year: float
    annualized_capex_h2_eur_per_year: float
    opex_fixed_bess_h2_eur_per_year: float
    bess_capacity_kwh: float
    electrolyzer_capacity_kw: float
    fuel_cell_capacity_kw: float
    tank_capacity_kg: float
    annual_grid_import_kwh: float
    annual_grid_export_kwh: float
    annual_pv_curtailed_kwh: float
    annual_pv_curtailed_share_of_available: float
    annual_h2_produced_kg: float
    annual_h2_used_kg: float
    bess_installed: bool
    h2_installed: bool


def extract_timeseries_and_kpis(model: pyo.ConcreteModel, df_input: pd.DataFrame) -> tuple[pd.DataFrame, HybridRunKpis]:
    """Extract hourly variables and annual KPIs from a solved model."""
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

    grid_exchange_eur = float(
        (timeseries["grid_import_kwh"] * timeseries["price_buy_eur_kwh"]).sum()
        - (timeseries["grid_export_kwh"] * timeseries["price_sell_eur_kwh"]).sum()
    )

    variable_opex_bess_h2_eur = float(
        pyo.value(model.bess_opex_variable_eur_per_kwh_throughput)
        * (timeseries["bess_charged_kwh"] + timeseries["bess_discharged_kwh"]).sum()
        + pyo.value(model.ely_opex_variable_eur_per_kwh_input)
        * (timeseries["p_ely_kw"] * dt_h).sum()
        + pyo.value(model.fc_opex_variable_eur_per_kwh_output)
        * (timeseries["p_fc_kw"] * dt_h).sum()
        + pyo.value(model.tank_opex_variable_eur_per_kg_throughput)
        * (timeseries["h2_produced_kg"] + timeseries["h2_used_kg"]).sum()
    )
    opex_eur = grid_exchange_eur + variable_opex_bess_h2_eur
    tac_eur = float(pyo.value(model.objective))

    bess_add_kwh = float(pyo.value(model.bess_add_kwh))
    bess_total_kwh = bess_add_kwh

    annualized_capex_bess_eur = float(bess_add_kwh * pyo.value(model.bess_ann_eur_per_kwh_year))
    annualized_capex_h2_eur = float(
        pyo.value(model.ely_capacity_kw) * pyo.value(model.ely_ann_eur_per_kw_year)
        + pyo.value(model.fc_capacity_kw) * pyo.value(model.fc_ann_eur_per_kw_year)
        + pyo.value(model.tank_capacity_kg) * pyo.value(model.tank_ann_eur_per_kg_year)
    )
    opex_fixed_bess_h2_eur = float(
        bess_add_kwh * pyo.value(model.bess_opex_fixed_eur_per_kwh_year)
        + pyo.value(model.ely_capacity_kw) * pyo.value(model.ely_opex_fixed_eur_per_kw_year)
        + pyo.value(model.fc_capacity_kw) * pyo.value(model.fc_opex_fixed_eur_per_kw_year)
        + pyo.value(model.tank_capacity_kg) * pyo.value(model.tank_opex_fixed_eur_per_kg_year)
    )

    ely_capacity_kw = float(pyo.value(model.ely_capacity_kw))
    fc_capacity_kw = float(pyo.value(model.fc_capacity_kw))
    tank_capacity_kg = float(pyo.value(model.tank_capacity_kg))
    annual_h2_produced = float(timeseries["h2_produced_kg"].sum())
    annual_h2_used = float(timeseries["h2_used_kg"].sum())

    # H2 is considered installed only if ALL three components are present
    # at feasible minimum levels AND H2 is actually produced and consumed
    h2_installed = (
        (ely_capacity_kw >= 1.0)
        and (fc_capacity_kw >= 1.0)
        and (tank_capacity_kg >= 5.0)
        and (annual_h2_produced >= 1.0)
        and (annual_h2_used >= 1.0)
    )

    if not h2_installed:
        ely_capacity_kw = 0.0
        fc_capacity_kw = 0.0
        tank_capacity_kg = 0.0
        annual_h2_produced = 0.0
        annual_h2_used = 0.0

        h2_var_opex_noise = float(
            pyo.value(model.ely_opex_variable_eur_per_kwh_input) * (timeseries["p_ely_kw"] * dt_h).sum()
            + pyo.value(model.fc_opex_variable_eur_per_kwh_output) * (timeseries["p_fc_kw"] * dt_h).sum()
            + pyo.value(model.tank_opex_variable_eur_per_kg_throughput) * (timeseries["h2_produced_kg"] + timeseries["h2_used_kg"]).sum()
        )
        bess_fixed_opex_only = float(bess_add_kwh * pyo.value(model.bess_opex_fixed_eur_per_kwh_year))
        h2_fixed_opex_noise = opex_fixed_bess_h2_eur - bess_fixed_opex_only

        tac_eur -= (annualized_capex_h2_eur + h2_fixed_opex_noise + h2_var_opex_noise)
        opex_eur -= h2_var_opex_noise
        annualized_capex_h2_eur = 0.0
        opex_fixed_bess_h2_eur = bess_fixed_opex_only

    kpis = HybridRunKpis(
        achieved_ssr=(1.0 - annual_grid_import_kwh / annual_demand_kwh) if annual_demand_kwh > 0 else 0.0,
        tac_eur_per_year=tac_eur,
        opex_eur_per_year=opex_eur,
        annualized_capex_bess_eur_per_year=annualized_capex_bess_eur,
        annualized_capex_h2_eur_per_year=annualized_capex_h2_eur,
        opex_fixed_bess_h2_eur_per_year=opex_fixed_bess_h2_eur,
        bess_capacity_kwh=bess_total_kwh,
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
        bess_installed=bess_add_kwh > 1e-6,
        h2_installed=h2_installed,
    )

    return timeseries, kpis
