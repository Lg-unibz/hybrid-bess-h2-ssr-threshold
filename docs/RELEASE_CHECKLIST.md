# Release Checklist

- Run `python scripts/run_demo.py`.
- Confirm `results/demo/demo_summary.csv` and `results/demo/demo_capacities.csv` are created.
- Run `python scripts/run_paper_scale.py` and confirm it reports the expected missing confidential inputs without submitting jobs.
- Inspect tracked files with `git status --short` and `git ls-files`.
- Confirm no confidential demand CSVs are tracked.
- Confirm no raw private company data are tracked.
- Search for absolute paths, usernames, credentials, solver license paths, and private notes.
- Search for `.log`, `.sol`, `.lp`, `.mps`, `.slurm`, `.out`, `.err`, `.env`, and license files.
- Confirm the local alpha-test guide exists at `docs/LOCAL_ALPHA_TEST.md`.
- Check `README.md`, `DATA_AVAILABILITY.md`, and `REPRODUCIBILITY.md`.
- Check `CITATION.cff` and update authors/DOI if available.
- Check `requirements.txt`, `requirements-gurobi.txt`, and `environment.yml`.
- Confirm PVGIS/PUN redistribution terms before adding processed public-source files.
- Create a GitHub release tagged `v1.0.0-paper-submission`.
- Optionally archive the release on Zenodo and update `CITATION.cff` with the DOI.

