# Non-Confidential Aggregated Paper Outputs

This folder contains the complete suite of non-confidential aggregate tabular outputs supporting the manuscript. All files report macro-level economic, technical, sensitivity, and structural stress-test indicators. They contain no confidential hourly company load data.

## Included Datasets

1. **`tab1_pun_statistics.csv`** (PUN market statistics):
   Annual hourly market electricity purchase tariff statistics for the Italian Single National Price (PUN) across 10 historical years (2015–2024, official GME data), reporting mean, standard deviation, minimum, maximum, zero-price hours, and scenario role.

2. **`tab2_baseline_assumptions.csv`** (Baseline techno-economic assumptions):
   Audited techno-economic assumptions and financial contracts (CAPEX, efficiencies, replacement schedules, WACC, lifetime) for solar PV, BESS, electrolyzer, fuel cell, hydrogen tank, and grid exchange.

3. **`tab3_structural_stress_summary.csv`** (Structural stress-test summary):
   Full-factorial structural stress-test results across 27 combinations of weather chronology (2014, 2018, 2007), PV scale (0.69×, 1.00×, 1.31×), and grid limits (0.5×, 1.0×, 1.5×). Reports first emergence ($SSR_{\text{emerge}}$), $\Delta SSR$, relative shift, maximum feasible SSR, and TAC at maximum feasibility.

4. **`tab_d1_weather_descriptors.csv`** (Weather descriptor screening):
   Multivariate weather descriptor screening across all 16 PVGIS meteorological years (2005–2020), documenting $I_1$ (solar-to-demand ratio), $I_2$ (direct PV coverage fraction), $I_3$ (excess-PV energy ratio), distance to centroid $D_i$, and signed favorability score $F_i$.

5. **`tab_d2_ofat_elasticities.csv`** (OFAT sensitivity metrics & elasticities):
   One-factor-at-a-time (OFAT) sensitivity metrics across the 9 primary techno-economic drivers, documenting low/base/high parameters, emergence thresholds $s_j^-$ and $s_j^+$, shift [pp], and range-normalized mean elasticity $\bar{S}_j$.

6. **`tab_d3_baseline_paired_tac.csv`** (Baseline paired TAC comparison):
   Paired baseline comparison between BESS-only and Hybrid BESS+H2 architectures across the 65%–100% SSR range for reference weather year 2018, including Total Annual Cost, $\Delta\mathrm{TAC}$ savings, and installed capacities.

7. **`tab_d4_capacity_bounds_and_mipgap.csv`** (Solver certificate & robustness audit):
   Solver certificate audit, relative MIP gap robustness verification across $0.005\%$ to $0.1\%$, and certified global component capacity bounds.

8. **`baseline_trajectory_2018.csv`**:
   Complete 1% fine-grid baseline paired simulation trajectory from 51% to 100% SSR for reference weather year 2018.


