# Figure Reproduction

The manuscript figures are based on the full paper-scale campaign. Exact reproduction requires the confidential full-year demand profile unless a figure is generated only from aggregate outputs.

The public companion is intended for local demo validation and aggregate figure inspection. It does not reproduce the annual paper-scale optimisation results on its own.

## Demo Figure

```bash
python scripts/run_demo.py
```

Writes `results/demo/figures/demo_capacities.png`.

This demo figure is a local synthetic-check output, not the manuscript's annual result set.

## Paper Figures And Tables

| Manuscript item | Public status | Inputs | Notes |
|---|---|---|---|
| Case-study demand/PV profile figures | Not exactly reproducible publicly | Confidential demand plus PVGIS | Do not publish hourly or detailed measured demand. |
| SSR workflow/method figure | Reproducible from documentation/code | `src/optimization/`, `configs/paper_scenarios.json` | No confidential data required. |
| Baseline TAC-SSR transition | Requires confidential full-year demand for exact rerun | private campaign `run_summary` | Can be inspected from aggregate exports. |
| Weather robustness figure | Requires confidential full-year demand for exact rerun | private campaign `run_summary`, PVGIS representative years | Aggregate threshold table can be exported. |
| H2 threshold drivers | Reproducible from aggregate `run_summary` export | `h2_thresholds_by_scenario_weather.csv` | Export with `src.analysis.export_paper_aggregates`. |
| TAC-shift heatmap | Reproducible from aggregate `run_summary` export | `tac_shift_median_year.csv` | Export from private summary. |
| Component-substitution heatmaps | Reproducible from aggregate `run_summary` export | `component_substitution_*_ssr_median_year.csv` | Export from private summary. |
| Worst-case boundary | Requires confidential full-year demand for exact rerun | private campaign `run_summary` | Feasibility summary can be exported. |

The public companion should only be used to check the method figure, the demo figure, and aggregate tables that do not expose hourly demand.

## Aggregate Export Command

```bash
python -m src.analysis.export_paper_aggregates /path/to/run_summary_merged.csv --output-dir results/paper_aggregated
```

Review exported CSVs before release to confirm that they contain no hourly demand series or private identifiers.

