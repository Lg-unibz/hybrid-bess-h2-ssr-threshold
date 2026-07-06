# Hybrid BESS-H2 SSR Threshold Public Companion

This repository is a public, reviewer-facing companion for a Journal of Energy Storage manuscript on the transition from battery-only storage to hybrid battery-hydrogen storage in a grid-connected PV prosumer.

The full paper-scale campaign was originally executed on an HPC cluster through Slurm. Those cluster-specific submission scripts are not included here. This public companion is designed to be downloaded and tested locally in isolation.

The model is a mixed-integer linear program (MILP) that jointly optimizes storage sizing and hourly dispatch under self-sufficiency ratio (SSR) constraints.

## What Is Included

- Core MILP model code for the hybrid BESS-H2 sizing and dispatch problem.
- Scenario and financial helper code used to assemble technical and economic assumptions.
- A fully synthetic four-season demo dataset with four representative weeks.
- A runnable demo workflow under `scripts/run_demo.py`.
- A safe paper-scale preflight helper under `scripts/run_paper_scale.py`.
- Public documentation for data restrictions and reproducibility levels.
- A helper to export non-confidential paper aggregate CSVs from a private `run_summary` file.
- One non-confidential baseline aggregate table from the manuscript.

## What Is Not Included

The confidential full-year measured electricity-demand profile is not included. Raw private company data, private site identifiers, exact coordinates, internal HPC paths, Slurm logs, solver files, credentials, and license files are also excluded.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_demo.py
```

The demo is intended for local execution on the synthetic dataset only. It does not reproduce the annual manuscript results.

The demo writes:

- `results/demo/demo_summary.csv`
- `results/demo/demo_capacities.csv`
- `results/demo/figures/demo_capacities.png`
- one dispatch time-series CSV per demo run

The default open-source solver path uses Pyomo with HiGHS. Gurobi can also be used if installed and licensed:

```bash
pip install -r requirements-gurobi.txt
python scripts/run_demo.py --solver gurobi
```

## Repository Structure

```text
configs/                  Clean public configuration files
data/demo/                Synthetic seasonal-week demo data
data/public_sources/      Notes on PVGIS and PUN sources
data/schemas/             Demo CSV schema
docs/                     Reproduction and release documentation
results/demo/             Demo outputs
results/paper_aggregated/ Non-confidential aggregate paper outputs
scripts/                  Demo, data-generation, and preflight scripts
src/                      Model, solver, scenario, loader, and export code
```

## Full Paper-Scale Workflow

Exact paper-scale reruns require inputs that are not public and were originally run through HPC/Slurm:

- `input/processed/electricity_demand/csv/2024_h.csv`
- `input/processed/pv_production/csv/production_global_2005.csv`
- `input/processed/pv_production/csv/production_global_2011.csv`
- `input/processed/pv_production/csv/production_global_2014.csv`
- `input/processed/prices/csv/pun_2020.csv`
- `input/processed/prices/csv/pun_2022.csv`
- `input/processed/prices/csv/pun_2024.csv`

Run the paper-scale preflight with:

```bash
python scripts/run_paper_scale.py
```

This is a validation step only. It reports the expected confidential/full-scale inputs and does not submit Slurm jobs or start the optimisation campaign.

## Data Availability

See `DATA_AVAILABILITY.md`. The demo data are synthetic. The PVGIS and PUN inputs are public-source data products, but this repository does not redistribute full processed source files.

The full annual demand series remains confidential and is not public in this companion repository.

## Citation

See `CITATION.cff`. The DOI is intentionally left blank until Zenodo or GitHub generates one.

## License

Code and synthetic demo data are released under the license in `LICENSE`, subject to manuscript and institutional approval before public posting.

## Contact

For questions regarding this repository or the associated manuscript, please contact the corresponding author:

**Lorenzo Gambadori**  
Faculty of Engineering, Free University of Bozen--Bolzano  
Email: [lorenzo.gambadori@student.unibz.it](mailto:lorenzo.gambadori@student.unibz.it)

## Local Alpha Test

See `docs/LOCAL_ALPHA_TEST.md` for an isolated local validation workflow after downloading this folder from the HPC system.

