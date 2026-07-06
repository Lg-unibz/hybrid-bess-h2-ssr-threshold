# Aggregated Paper Outputs

This folder is reserved for non-confidential aggregate outputs that support the manuscript.

Included:

- `baseline_absolute_values_median_year.csv`: aggregate baseline values from the manuscript table. It contains costs and capacities only, not hourly demand data.

Not included in this checkout because the merged private `run_summary` file is not present:

- `h2_thresholds_by_scenario_weather.csv`
- `tac_shift_median_year.csv`
- `tac_shift_weather_ranges.csv`
- `component_substitution_80_ssr_median_year.csv`
- `component_substitution_90_ssr_median_year.csv`
- `component_substitution_100_ssr_median_year.csv`
- `worst_case_feasibility_summary.csv`

To export those files from a private, complete campaign output, run:

```bash
python -m src.analysis.export_paper_aggregates /path/to/run_summary_merged.csv --output-dir results/paper_aggregated
```

Before committing exported files, verify that they contain only scenario labels, weather-year labels, capacities, costs, threshold metrics, feasibility statuses, and similar aggregate values.

