# US Election County-Level Swing Analysis

What county-level demographic and economic conditions predicted the 2020-to-2024 partisan swing? This project builds a multilevel model to answer that question, with a focus on whether the effect of educational composition depends on local economic context.

## What the data shows so far

Across 3,111 counties (excluding Alaska), the average county swung +1.7 percentage points toward Republicans in 2024 compared to 2020. But the variation is large, and the patterns are not uniform.

- Counties with higher college attainment swung less Republican (r = -0.35). Education is the strongest single demographic predictor of swing direction.
- Counties with larger Hispanic populations swung more Republican (r = 0.31), consistent with the widely discussed Latino rightward shift in 2024.
- Rural counties swung Republican more than urban ones, with a clear gradient across the six NCHS urban-rural categories.
- A baseline OLS model using nine demographic predictors explains about 35% of the county-level variance in swing, with college share, Hispanic share, and 2020 baseline partisanship as the strongest predictors.
- State-level unemployment change (2020-2024) is now available for all 51 states and will serve as the Level-2 variable for the cross-level interaction in the multilevel model.

## Data sources

- **Election returns**: MIT Election Data + Science Lab (MEDSL) county presidential returns, 2000-2024. Harvard Dataverse, DOI: 10.7910/DVN/VOQCHQ.
- **Demographics**: American Community Survey 5-year estimates (2019-2023 vintage) via the Census API.
- **State unemployment**: Bureau of Labor Statistics, Local Area Unemployment Statistics (LAUS).
- **Urban-rural classification**: NCHS 2013 urban-rural scheme (6 categories).
- **Land area**: Census 2024 county gazetteer.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a free Census API key at https://api.census.gov/data/key_signup.html and set it:
   ```
   export CENSUS_API_KEY=your_key_here
   ```

3. Run the notebooks in order:
   ```
   jupyter notebook notebooks/01_data_acquisition.ipynb
   jupyter notebook notebooks/02_data_preparation.ipynb
   jupyter notebook notebooks/03_exploratory_analysis.ipynb
   ```

The first notebook downloads all raw data (~50 MB total). The second merges everything into `data/processed/county_swing_dataset.csv`. The third produces figures and a baseline OLS regression.

## Project structure

```
data/raw/              Raw downloaded files (not tracked in git)
data/processed/        Merged analysis-ready CSV
notebooks/             Numbered notebooks for each pipeline step
src/                   Download and cleaning functions
figures/               Output plots
```

## Notes

- Alaska is flagged but kept in the dataset. Its boroughs use a different reporting structure than standard counties, so most models should exclude it.
- Connecticut reorganized its counties in 2022. Some counties may not merge cleanly with the 2023 ACS data.
- Virginia independent cities are county-equivalents with their own FIPS codes and work fine in the merge.
