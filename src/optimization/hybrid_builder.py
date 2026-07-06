from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import pyomo.environ as pyo

from src.config.constants import H2_LHV_KWH_KG
from src.optimization.constraints import max_grid_import_from_ssr


@dataclass(frozen=True)
class HybridEconomicInputs:
    """Annualized and operational coefficients used in the MILP objective."""

    bess_annualized_eur_per_kwh_year: float
    ely_annualized_eur_per_kw_year: float
    fc_annualized_eur_per_kw_year: float
    tank_annualized_eur_per_kg_year: float
    bess_opex_fixed_eur_per_kwh_year: float
    ely_opex_fixed_eur_per_kw_year: float
    fc_opex_fixed_eur_per_kw_year: float
    tank_opex_fixed_eur_per_kg_year: float
    bess_opex_variable_eur_per_kwh_throughput: float
    ely_opex_variable_eur_per_kwh_input: float
    fc_opex_variable_eur_per_kwh_output: float
    tank_opex_variable_eur_per_kg_throughput: float


@dataclass(frozen=True)
class HybridTechnicalInputs:
    """Technical assumptions used by the integrated BESS+H2 model."""

    timestep_hours: float
    bess_eta_roundtrip: float
    bess_soc_min_fraction: float
    bess_soc_max_fraction: float
    bess_self_discharge_fraction_per_hour: float
    bess_default_c_rate_kw_per_kwh: float
    bess_capacity_upper_bound_kwh: float

    grid_max_import_kw: float
    grid_max_export_kw: float

    eta_ely: float
    eta_fc: float
    ely_min_load_fraction: float
    ely_capacity_upper_bound_kw: float
    fc_capacity_upper_bound_kw: float
    tank_capacity_upper_bound_kg: float
    tank_min_soc_fraction: float


@dataclass(frozen=True)
class HybridModelInputs:
    """All inputs required to build and solve one integrated hybrid run."""

    study_id: str
    run_mode: str
    ssr_target: float | None
    df: pd.DataFrame
    technical: HybridTechnicalInputs
    economics: HybridEconomicInputs


def build_hybrid_model(inputs: HybridModelInputs) -> pyo.ConcreteModel:
    """Build one integrated hybrid MILP with optional SSR epsilon-constraint.

    Governing electricity node equation:
    PV_used + BESS_dis + Grid_buy + FC = Load + BESS_ch + Grid_sell + Ely.
    """
    tcfg = inputs.technical
    ecfg = inputs.economics
    df = inputs.df.copy()

    dt_h = tcfg.timestep_hours
    n_steps = len(df)

    pv_kw = (df["pv_production_kwh"] / dt_h).to_list()
    demand_kw = (df["demand_kwh"] / dt_h).to_list()
    price_buy = df["price_buy_eur_kwh"].to_list()
    price_sell = df["price_sell_eur_kwh"].to_list()

    eta_ch = tcfg.bess_eta_roundtrip**0.5
    eta_dis = tcfg.bess_eta_roundtrip**0.5

    c_rate = tcfg.bess_default_c_rate_kw_per_kwh

    p_ch_upper = c_rate * tcfg.bess_capacity_upper_bound_kwh
    p_dis_upper = c_rate * tcfg.bess_capacity_upper_bound_kwh
    soc_upper = tcfg.bess_soc_max_fraction * tcfg.bess_capacity_upper_bound_kwh

    m = pyo.ConcreteModel(name=f"hybrid_{inputs.study_id}_{inputs.run_mode}")
    m.T = pyo.Set(initialize=range(n_steps), ordered=True)

    m.dt_h = pyo.Param(initialize=dt_h)
    m.pv_kw = pyo.Param(m.T, initialize=dict(enumerate(pv_kw)))
    m.demand_kw = pyo.Param(m.T, initialize=dict(enumerate(demand_kw)))
    m.price_buy_eur_kwh = pyo.Param(m.T, initialize=dict(enumerate(price_buy)))
    m.price_sell_eur_kwh = pyo.Param(m.T, initialize=dict(enumerate(price_sell)))

    m.eta_ch = pyo.Param(initialize=eta_ch)
    m.eta_dis = pyo.Param(initialize=eta_dis)
    m.bess_self_discharge = pyo.Param(initialize=tcfg.bess_self_discharge_fraction_per_hour)
    m.bess_soc_min = pyo.Param(initialize=tcfg.bess_soc_min_fraction)
    m.bess_soc_max = pyo.Param(initialize=tcfg.bess_soc_max_fraction)
    m.bess_c_rate = pyo.Param(initialize=c_rate)

    m.grid_max_import_kw = pyo.Param(initialize=tcfg.grid_max_import_kw)
    m.grid_max_export_kw = pyo.Param(initialize=tcfg.grid_max_export_kw)

    m.eta_ely = pyo.Param(initialize=tcfg.eta_ely)
    m.eta_fc = pyo.Param(initialize=tcfg.eta_fc)
    m.ely_min_load = pyo.Param(initialize=tcfg.ely_min_load_fraction)
    m.h2_lhv_kwh_per_kg = pyo.Param(initialize=H2_LHV_KWH_KG)
    m.tank_min_soc = pyo.Param(initialize=tcfg.tank_min_soc_fraction)

    m.bess_ann_eur_per_kwh_year = pyo.Param(initialize=ecfg.bess_annualized_eur_per_kwh_year)
    m.ely_ann_eur_per_kw_year = pyo.Param(initialize=ecfg.ely_annualized_eur_per_kw_year)
    m.fc_ann_eur_per_kw_year = pyo.Param(initialize=ecfg.fc_annualized_eur_per_kw_year)
    m.tank_ann_eur_per_kg_year = pyo.Param(initialize=ecfg.tank_annualized_eur_per_kg_year)
    m.bess_opex_fixed_eur_per_kwh_year = pyo.Param(initialize=ecfg.bess_opex_fixed_eur_per_kwh_year)
    m.ely_opex_fixed_eur_per_kw_year = pyo.Param(initialize=ecfg.ely_opex_fixed_eur_per_kw_year)
    m.fc_opex_fixed_eur_per_kw_year = pyo.Param(initialize=ecfg.fc_opex_fixed_eur_per_kw_year)
    m.tank_opex_fixed_eur_per_kg_year = pyo.Param(initialize=ecfg.tank_opex_fixed_eur_per_kg_year)
    m.bess_opex_variable_eur_per_kwh_throughput = pyo.Param(
        initialize=ecfg.bess_opex_variable_eur_per_kwh_throughput
    )
    m.ely_opex_variable_eur_per_kwh_input = pyo.Param(
        initialize=ecfg.ely_opex_variable_eur_per_kwh_input
    )
    m.fc_opex_variable_eur_per_kwh_output = pyo.Param(
        initialize=ecfg.fc_opex_variable_eur_per_kwh_output
    )
    m.tank_opex_variable_eur_per_kg_throughput = pyo.Param(
        initialize=ecfg.tank_opex_variable_eur_per_kg_throughput
    )

    m.bess_add_kwh = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, tcfg.bess_capacity_upper_bound_kwh))
    m.ely_capacity_kw = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, tcfg.ely_capacity_upper_bound_kw))
    m.fc_capacity_kw = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, tcfg.fc_capacity_upper_bound_kw))
    m.tank_capacity_kg = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, tcfg.tank_capacity_upper_bound_kg))

    m.soc_start_kwh = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, soc_upper))
    m.tank_start_kg = pyo.Var(within=pyo.NonNegativeReals, bounds=(0.0, tcfg.tank_capacity_upper_bound_kg))

    m.p_bess_ch_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, p_ch_upper))
    m.p_bess_dis_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, p_dis_upper))
    m.bess_soc_kwh = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, soc_upper))
    m.u_bess_ch = pyo.Var(m.T, within=pyo.Binary)
    m.u_bess_dis = pyo.Var(m.T, within=pyo.Binary)

    m.p_pv_used_kw = pyo.Var(m.T, within=pyo.NonNegativeReals)
    m.p_pv_curtailed_kw = pyo.Var(m.T, within=pyo.NonNegativeReals)

    m.p_grid_buy_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, tcfg.grid_max_import_kw))
    m.p_grid_sell_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, tcfg.grid_max_export_kw))

    m.p_ely_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, tcfg.ely_capacity_upper_bound_kw))
    m.p_fc_kw = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, tcfg.fc_capacity_upper_bound_kw))
    m.tank_mass_kg = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=(0.0, tcfg.tank_capacity_upper_bound_kg))
    m.u_ely = pyo.Var(m.T, within=pyo.Binary)

    def _c_pv_split(model: pyo.ConcreteModel, t: int) -> Any:
        return model.p_pv_used_kw[t] + model.p_pv_curtailed_kw[t] == model.pv_kw[t]

    m.c_pv_split = pyo.Constraint(m.T, rule=_c_pv_split)

    def _c_power_balance(model: pyo.ConcreteModel, t: int) -> Any:
        return (
            model.p_pv_used_kw[t] + model.p_bess_dis_kw[t] + model.p_grid_buy_kw[t] + model.p_fc_kw[t]
            == model.demand_kw[t] + model.p_bess_ch_kw[t] + model.p_grid_sell_kw[t] + model.p_ely_kw[t]
        )

    m.c_power_balance = pyo.Constraint(m.T, rule=_c_power_balance)

    def _c_bess_soc(model: pyo.ConcreteModel, t: int) -> Any:
        soc_prev = model.soc_start_kwh if t == 0 else model.bess_soc_kwh[t - 1]
        return model.bess_soc_kwh[t] == (
            soc_prev * (1.0 - model.bess_self_discharge * dt_h)
            + model.eta_ch * model.p_bess_ch_kw[t] * dt_h
            - (1.0 / model.eta_dis) * model.p_bess_dis_kw[t] * dt_h
        )

    m.c_bess_soc = pyo.Constraint(m.T, rule=_c_bess_soc)

    def _c_bess_soc_low(model: pyo.ConcreteModel, t: int) -> Any:
        return model.bess_soc_kwh[t] >= model.bess_soc_min * model.bess_add_kwh

    def _c_bess_soc_up(model: pyo.ConcreteModel, t: int) -> Any:
        return model.bess_soc_kwh[t] <= model.bess_soc_max * model.bess_add_kwh

    m.c_bess_soc_low = pyo.Constraint(m.T, rule=_c_bess_soc_low)
    m.c_bess_soc_up = pyo.Constraint(m.T, rule=_c_bess_soc_up)

    m.c_bess_ch_big_m = pyo.Constraint(m.T, rule=lambda model, t: model.p_bess_ch_kw[t] <= p_ch_upper * model.u_bess_ch[t])
    m.c_bess_dis_big_m = pyo.Constraint(m.T, rule=lambda model, t: model.p_bess_dis_kw[t] <= p_dis_upper * model.u_bess_dis[t])
    m.c_bess_ch_cap = pyo.Constraint(m.T, rule=lambda model, t: model.p_bess_ch_kw[t] <= model.bess_c_rate * model.bess_add_kwh)
    m.c_bess_dis_cap = pyo.Constraint(m.T, rule=lambda model, t: model.p_bess_dis_kw[t] <= model.bess_c_rate * model.bess_add_kwh)
    m.c_bess_mode = pyo.Constraint(m.T, rule=lambda model, t: model.u_bess_ch[t] + model.u_bess_dis[t] <= 1)

    m.c_soc_start_low = pyo.Constraint(expr=m.soc_start_kwh >= m.bess_soc_min * m.bess_add_kwh)
    m.c_soc_start_up = pyo.Constraint(expr=m.soc_start_kwh <= m.bess_soc_max * m.bess_add_kwh)
    m.c_soc_cycle = pyo.Constraint(expr=m.bess_soc_kwh[n_steps - 1] >= m.soc_start_kwh)

    def _c_tank_balance(model: pyo.ConcreteModel, t: int) -> Any:
        m_prev = model.tank_start_kg if t == 0 else model.tank_mass_kg[t - 1]
        m_in_kg = (model.p_ely_kw[t] * model.eta_ely / model.h2_lhv_kwh_per_kg) * dt_h
        m_out_kg = (model.p_fc_kw[t] / (model.eta_fc * model.h2_lhv_kwh_per_kg)) * dt_h
        return model.tank_mass_kg[t] == m_prev + m_in_kg - m_out_kg

    m.c_tank_balance = pyo.Constraint(m.T, rule=_c_tank_balance)
    m.c_tank_low = pyo.Constraint(m.T, rule=lambda model, t: model.tank_mass_kg[t] >= model.tank_min_soc * model.tank_capacity_kg)
    m.c_tank_up = pyo.Constraint(m.T, rule=lambda model, t: model.tank_mass_kg[t] <= model.tank_capacity_kg)
    m.c_tank_start_low = pyo.Constraint(expr=m.tank_start_kg >= m.tank_min_soc * m.tank_capacity_kg)
    m.c_tank_start_up = pyo.Constraint(expr=m.tank_start_kg <= m.tank_capacity_kg)
    m.c_tank_cycle = pyo.Constraint(expr=m.tank_mass_kg[n_steps - 1] >= m.tank_start_kg)

    m.c_ely_cap = pyo.Constraint(m.T, rule=lambda model, t: model.p_ely_kw[t] <= model.ely_capacity_kw)
    m.c_ely_mode = pyo.Constraint(
        m.T,
        rule=lambda model, t: model.p_ely_kw[t] <= tcfg.ely_capacity_upper_bound_kw * model.u_ely[t],
    )
    m.c_ely_min_load = pyo.Constraint(
        m.T,
        rule=lambda model, t: model.p_ely_kw[t]
        >= model.ely_min_load * model.ely_capacity_kw
        - model.ely_min_load * tcfg.ely_capacity_upper_bound_kw * (1 - model.u_ely[t]),
    )
    m.c_fc_up = pyo.Constraint(m.T, rule=lambda model, t: model.p_fc_kw[t] <= model.fc_capacity_kw)

    if inputs.ssr_target is not None:
        max_grid_import_kwh = max_grid_import_from_ssr(float(df["demand_kwh"].sum()), inputs.ssr_target)
        m.c_ssr_target = pyo.Constraint(expr=sum(m.p_grid_buy_kw[t] for t in m.T) * dt_h <= max_grid_import_kwh)

    def _objective(model: pyo.ConcreteModel) -> Any:
        grid_exchange_eur = sum(
            (
                model.price_buy_eur_kwh[t] * model.p_grid_buy_kw[t]
                - model.price_sell_eur_kwh[t] * model.p_grid_sell_kw[t]
            )
            * dt_h
            for t in model.T
        )

        variable_opex_bess_h2_eur = sum(
            model.bess_opex_variable_eur_per_kwh_throughput
            * (model.p_bess_ch_kw[t] + model.p_bess_dis_kw[t])
            * dt_h
            + model.ely_opex_variable_eur_per_kwh_input * model.p_ely_kw[t] * dt_h
            + model.fc_opex_variable_eur_per_kwh_output * model.p_fc_kw[t] * dt_h
            + model.tank_opex_variable_eur_per_kg_throughput
            * (
                (model.p_ely_kw[t] * model.eta_ely / model.h2_lhv_kwh_per_kg)
                + (model.p_fc_kw[t] / (model.eta_fc * model.h2_lhv_kwh_per_kg))
            )
            * dt_h
            for t in model.T
        )

        ann_capex_bess_eur = model.bess_add_kwh * model.bess_ann_eur_per_kwh_year
        ann_capex_h2_eur = (
            model.ely_capacity_kw * model.ely_ann_eur_per_kw_year
            + model.fc_capacity_kw * model.fc_ann_eur_per_kw_year
            + model.tank_capacity_kg * model.tank_ann_eur_per_kg_year
        )
        annualized_capex_total_eur = ann_capex_bess_eur + ann_capex_h2_eur

        opex_fixed_bess_h2_eur = (
            model.bess_add_kwh * model.bess_opex_fixed_eur_per_kwh_year
            + model.ely_capacity_kw * model.ely_opex_fixed_eur_per_kw_year
            + model.fc_capacity_kw * model.fc_opex_fixed_eur_per_kw_year
            + model.tank_capacity_kg * model.tank_opex_fixed_eur_per_kg_year
        )

        # TAC = annualized CAPEX + fixed OPEX + variable OPEX + grid exchange.
        return (
            annualized_capex_total_eur
            + opex_fixed_bess_h2_eur
            + variable_opex_bess_h2_eur
            + grid_exchange_eur
        )

    m.objective = pyo.Objective(rule=_objective, sense=pyo.minimize)

    return m
