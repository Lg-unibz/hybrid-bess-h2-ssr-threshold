# Reproducibility

## A. Demo Reproducibility

The demo is fully executable with the included synthetic seasonal-week data on a local machine:

```bash
pip install -r requirements.txt
python scripts/run_demo.py
```

This verifies the model-building, solver, extraction, and output-writing path on a small non-confidential instance. It is a local alpha test only and does not reproduce the annual paper-scale results.

## B. Paper-Scale Preflight

The paper-scale workflow was originally executed on HPC through Slurm. The public repository does not ship those submission scripts.

Run the public preflight helper:

```bash
python scripts/run_paper_scale.py
```

The script validates the expected full-scale input paths, reports missing confidential files, and does not submit jobs.

## C. Paper-Result Inspection

Paper results can be inspected through non-confidential aggregate outputs in `results/paper_aggregated/`. The public helper:

```bash
python -m src.analysis.export_paper_aggregates /path/to/run_summary_merged.csv --output-dir results/paper_aggregated
```

exports aggregate tables from a private campaign summary without exporting hourly demand profiles.

## D. Full Paper-Scale Rerun

Exact reruns require:

- the confidential full-year hourly demand profile;
- processed PVGIS profiles for the representative weather years;
- processed PUN price profiles;
- a MILP solver such as Gurobi or HiGHS;
- the same scenario assumptions documented in `configs/paper_scenarios.json`.

The public repository documents the expected paths but does not include the confidential demand input.

If the confidential files are available on the original HPC system, the run can be re-created there with the private workflow. The public companion is intentionally limited to local demo execution and paper-scale path validation.

