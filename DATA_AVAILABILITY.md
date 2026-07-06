# Data Availability

## Confidential Demand Data

The full-year measured hourly electricity-demand profile from the agricultural facility is confidential and is not included in this public repository. The repository also excludes raw private company files, exact private site identifiers, and any internal paths or credentials.

The original annual paper-scale optimisation was executed on HPC through Slurm. The public companion does not redistribute those submission scripts.

The full paper-scale workflow expects the confidential demand file at:

```text
input/processed/electricity_demand/csv/2024_h.csv
```

That path is documented for reproducibility and inspection only. The file must not be committed to the public repository.

## Demo Data

The included demo dataset under `data/demo/seasonal_weeks/` is synthetic. It contains four one-week hourly profiles:

- winter week
- spring week
- summer week
- autumn week

The files preserve the model input schema but do not contain real measured demand values.

They are intended for local alpha testing and do not reproduce the annual manuscript results.

## Public PVGIS And PUN Sources

The paper-scale workflow uses PV production derived from PVGIS and electricity prices derived from public PUN records. Expected processed paths are:

```text
input/processed/pv_production/csv/production_global_2005.csv
input/processed/pv_production/csv/production_global_2011.csv
input/processed/pv_production/csv/production_global_2014.csv
input/processed/prices/csv/pun_2020.csv
input/processed/prices/csv/pun_2022.csv
input/processed/prices/csv/pun_2024.csv
```

Processed PVGIS/PUN files are not bundled here. If they are added later, include source attribution and check redistribution terms.

## Aggregated Outputs

`results/paper_aggregated/` may contain non-confidential aggregate metrics such as capacities, total annual cost, hydrogen-emergence thresholds, scenario labels, weather-year labels, and feasibility statuses. These files must not contain hourly demand data.

The included baseline table is an example aggregate export. Additional public aggregate CSVs can be added later only if they remain non-confidential.

## What Can Be Reproduced

- The synthetic demo workflow can be reproduced with included data.
- Paper-result inspection is possible through aggregate outputs included or exported from the private workflow.
- Exact paper-scale reruns require the confidential demand profile, public PVGIS/PUN inputs, and a suitable MILP solver environment.

