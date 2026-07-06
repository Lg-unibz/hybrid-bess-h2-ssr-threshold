# Local Alpha Test

Use this guide after downloading the public companion folder from the HPC system to a laptop or workstation.

## 1. Create A Clean Environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell or Command Prompt, activate with:

```powershell
.venv\Scripts\activate
```

If you want the optional Gurobi path, install the extra requirements after obtaining a valid Gurobi licence:

```bash
pip install -r requirements-gurobi.txt
```

## 2. Run Syntax Checks

```bash
python -m compileall src scripts
```

## 3. Run The Demo

```bash
python scripts/run_demo.py
```

Expected outputs:

- `results/demo/demo_summary.csv`
- `results/demo/demo_capacities.csv`
- `results/demo/figures/demo_capacities.png`

The demo is synthetic and non-confidential. It verifies the public workflow locally and is not meant to reproduce the annual paper-scale results.

## 4. Check Paper-Scale Preflight

```bash
python scripts/run_paper_scale.py
```

Expected behaviour:

- it reports the confidential/full-scale input paths that the original campaign expects;
- it reports which files are missing in the public repository;
- it does not crash;
- it does not submit Slurm jobs.

## 5. If A Solver Is Missing

The demo prefers an open-source Pyomo solver such as HiGHS. If no solver is available, expect an error stating that no MILP solver is available to Pyomo.

For the open-source path, install the dependencies from `requirements.txt`, which includes HiGHS support.

For Gurobi, install the optional requirements and configure a valid licence before running:

```bash
pip install -r requirements-gurobi.txt
python scripts/run_demo.py --solver gurobi
```

If Gurobi is not installed or not licensed, the demo should still work with HiGHS when available.

## 6. Package The Folder For Transfer

```bash
cd ..
tar --exclude='.venv' --exclude='__pycache__' -czf hybrid-bess-h2-ssr-threshold-public.tar.gz hybrid-bess-h2-ssr-threshold-public/
```

## 7. Final Checklist Before GitHub

- demo outputs created;
- no confidential data present;
- README consistent with local alpha-test instructions;
- GitHub URL updated if needed;
- `CITATION.cff` checked;
- `LICENSE` confirmed;
- release tag planned as `v1.0.0-paper-submission`.