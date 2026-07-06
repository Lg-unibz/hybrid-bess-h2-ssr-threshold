from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import pyomo.environ as pyo
from pyomo.opt import TerminationCondition
from pyomo.contrib.solver.common.util import NoFeasibleSolutionError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SolverSnapshot:
    """Serializable solver settings used for one run."""

    solver_name: str
    time_limit_s: int
    mip_gap: float


@dataclass(frozen=True)
class SolverOutcome:
    """Lightweight status payload extracted from SolverResults."""

    solver_status: str
    termination_condition: str
    objective_value: float | None
    elapsed_s: float


def solve_hybrid_model(
    model: pyo.ConcreteModel,
    solver_name: str,
    time_limit_s: int,
    mip_gap: float,
    tee: bool,
    study_id: str = "unknown",
    run_mode: str = "unknown",
    ssr_target: float | None = None,
) -> SolverOutcome:
    """Solve model and return a compact status payload with timing.
    
    Args:
        model: Pyomo ConcreteModel to solve.
        solver_name: Name of Pyomo solver factory (gurobi, highs, appsi_highs, cbc, glpk).
        time_limit_s: Wall-clock time limit in seconds.
        mip_gap: MIP relative optimality gap (0 = exact, >0 = relative tolerance).
        tee: If True, print solver output to console.
        study_id: Study case identifier for logging.
        run_mode: Run mode ("unconstrained" or f"ssr_{target_pct}") for logging.
        ssr_target: Self-sufficiency ratio target (if constrained run).
        
    Returns:
        SolverOutcome with status, termination condition, objective value, and elapsed time.
        
    Raises:
        RuntimeError: If solver is unavailable or terminates with unacceptable condition.
    """
    solver = pyo.SolverFactory(solver_name)
    if not solver.available():
        raise RuntimeError(f"Solver '{solver_name}' is not available")

    # Log pre-solve configuration
    logger.info(
        f"Starting solve: study_id={study_id} | run_mode={run_mode} | "
        f"ssr_target={ssr_target} | solver={solver_name} | "
        f"time_limit_s={time_limit_s} | mip_gap={mip_gap}"
    )

    # Configure solver options based on solver factory
    if solver_name == "gurobi":
        solver.options["TimeLimit"] = time_limit_s
        solver.options["MIPGap"] = mip_gap
    elif solver_name in {"highs", "appsi_highs"}:
        # HiGHS time limit is in seconds (float); mip_rel_gap is relative tolerance
        solver.options["time_limit"] = float(time_limit_s)
        solver.options["mip_rel_gap"] = mip_gap
    elif solver_name in {"cbc", "glpk"}:
        # CBC and GLPK use "sec" for time limit in seconds
        solver.options["sec"] = time_limit_s
    else:
        logger.warning(f"Unknown solver '{solver_name}': time limit may not be enforced")

    # Measure wall-clock time
    t_start = time.time()
    try:
        results = solver.solve(model, tee=tee)
    except NoFeasibleSolutionError as exc:
        # If time limit is reached before finding feasible solution,
        # Pyomo raises NoFeasibleSolutionError. Still extract solver status.
        logger.warning(
            f"NoFeasibleSolutionError during solve: {exc}. "
            f"This typically occurs when time limit is reached without finding a solution."
        )
        # Try to get partial results if available
        if hasattr(exc, 'results') and exc.results is not None:
            results = exc.results
        else:
            # Re-raise if we can't get any results
            raise
    
    elapsed_s = time.time() - t_start

    tc = results.solver.termination_condition
    accepted = {
        TerminationCondition.optimal,
        TerminationCondition.feasible,
        TerminationCondition.maxTimeLimit,
    }
    
    # Log post-solve outcome
    logger.info(
        f"Solve completed: study_id={study_id} | run_mode={run_mode} | "
        f"solver_status={results.solver.status} | termination={tc} | "
        f"elapsed_s={elapsed_s:.2f}"
    )
    
    if tc not in accepted:
        logger.error(
            f"Solver terminated with unacceptable condition: {tc} "
            f"(study_id={study_id}, run_mode={run_mode})"
        )
        raise RuntimeError(f"Solver terminated with condition: {tc}")

    objective_value: float | None = None
    try:
        objective_value = float(pyo.value(model.objective))
        logger.info(f"Objective value: {objective_value:.2e}")
    except Exception as exc:
        logger.warning(f"Could not extract objective value: {exc}")
        objective_value = None

    return SolverOutcome(
        solver_status=str(results.solver.status),
        termination_condition=str(results.solver.termination_condition),
        objective_value=objective_value,
        elapsed_s=elapsed_s,
    )
