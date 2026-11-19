# Hypertension treatment and public sports infrastructure across Korean districts, 2011-2024

Analysis code for the manuscript

> Kim S. *Did more public sports facilities mean less hypertension treatment in Korea?* (under review).

This archive contains code only. The processed district-year data, result tables, adjacency graph, and boundary files are available from the author on reasonable request. All source statistics are public.

Archived on Zenodo: https://doi.org/10.5281/zenodo.24356285

## Contents

| Path | What it is |
|---|---|
| `04_분석/HTN/sets_HTN_std3.json`, `04_분석/HTN/config_HTN_std3.json` | Prespecified covariates, expected directions, forced controls, and model configuration |
| `04_분석/HTN/MS/build/` | Scripts that read the result tables and write every number, table, and figure in the manuscript and the Supplemental Material |
| `01_스크립트/` | Analysis scripts (below) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment that describes its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Annual numbers of people treated for hypertensive disease (ICD-10 I10-I15, principal diagnosis), by district of residence: National Health Insurance Service, Regional Medical Care Utilization Statistics, 2011-2024.
- Mid-year population by 5-year age group: Ministry of the Interior and Safety, resident registration statistics. The 2023 age block of Changwon duplicated the 2022 block in the source file and was corrected (`population_override` in `sets_HTN_std3.json`).
- District covariates (physical activity, sports facilities, cardiometabolic behaviors, screening, social and economic indicators): Korean Statistical Information Service (KOSIS), the Community Health Survey, and NHIS statistics; sources are listed in Table S1 of the Supplemental Material.

## Pipeline

Scripts 36, 38, 39, 40 and 80 rebuild the expected counts and the panel from the master tables; their raw-input paths point to the author's local copies of the public source files and are kept for transparency. The analysis can be reproduced from step 4 with the processed files, which are available on request.

| Step | Script | Output |
|---|---|---|
| 1 | `36_build_national_agerates.py`, `38_build_Estd_all.py`, `39_build_Estd_fine.py` | National age rates and expected counts |
| 2 | `98_screen_std.py` | Spatial screening on age-standardized ratios |
| 3 | `80_build_disease_panel_v.py HTN` (`ST_VER=std3`) | Analytic panel |
| 4 | `81_fit_inla.R HTN` (`ST_VER=std3`, `ST_GRAPH=<adjacency graph>`, `ST_THREADS=1`) | Principal model, covariate-set comparison, 200-subset covariate-subset analysis, window models |
| 5 | `85_window_maps.R`, `86_yearly_maps_ehsa.py`, `86b_ehsa_modified_mk.py`, `87_window_grid.py` | Maps, emerging hot spot analysis |
| 6 | `88g_sens_prep.py HTN std3 GCA,INFECT` then `88g_sens_suite.R` (`GROUP=1..6`) | Sensitivity suite |
| 7 | `88h_ppc_varpart.R` | Posterior predictive checks, variance partition |
| 8 | `88k_struct_kh.R` with `kh_constraints.R` (Knorr-Held type II refitted with `KH_INIT=0`) | Knorr-Held I-IV with component-wise constraints, neighborhood and prior variants |
| 9 | `89g_sens_combine.py` | Combined sensitivity tables |
| 10 | `04_분석/HTN/MS/build/run_all.sh` | Manuscript, Supplemental Material, figures |

The adjacency graph and the boundary file (set `ST_SHP`) are not included and are available on request.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep 1.4.2 and sf 1.1.1; Python 3.9.6 with pandas 2.3.3, geopandas 1.0.1, numpy 2.0.2, matplotlib 3.9.4 and python-docx.

## Licence

Code: MIT License (`LICENSE`).

## Contact

Seongdae Kim, Hongik University (kimsd@hongik.ac.kr), ORCID 0000-0002-1525-0091
