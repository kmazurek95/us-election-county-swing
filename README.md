# US Election County-Level Swing Analysis

What county-level demographic and economic conditions predicted the 2020-to-2024 partisan swing? This project builds a multilevel model to answer that question, with a focus on whether the effect of educational composition depends on local economic context.

## Key findings

Across 3,111 counties (excluding Alaska), the average county swung +1.7 percentage points toward Republicans in 2024 compared to 2020. But the variation is large, and the patterns are not uniform.

**About 31% of swing variance is between states, not between counties.** An empty multilevel model (no predictors, just state grouping) yields an ICC of 0.305. County demographics alone miss a third of the story. Whatever drove the swing operated partly at the state level.

**Education is the strongest demographic predictor, and its effect varies by state.** A 10-percentage-point higher college share predicts about 0.60 pp less Republican swing (p < 1e-23). Adding a random slope on education improves the model significantly (LR chi2 = 72.4, p < 1e-16). In some states the education gradient was steep; in others it was nearly flat.

**Hispanic population share is the strongest positive predictor.** A 10-percentage-point higher Hispanic share predicts about 0.46 pp more Republican swing (p < 1e-71), consistent with the widely discussed Latino rightward shift.

**The cross-level interaction is not significant.** State-level unemployment change (2020-2024) does not explain why the education effect varies across states (interaction p = 0.48). The variation exists, but its source remains an open question.

**Model progression (all fit with ML for comparison):**
- Null model: AIC = -17,231
- Random intercepts + demographics: AIC = -18,506
- Random slope on education: AIC = -18,575
- Cross-level interaction: AIC = -18,572

Each step drops AIC substantially until the interaction model, where AIC actually ticks up (more parameters, no improvement in fit). The random slope model is the best fit: demographics matter, and the education effect is not uniform across states.

## Interactive dashboard

Run the Streamlit dashboard locally:
```
streamlit run app.py
```
It loads pre-computed model outputs and includes the caterpillar plot of state random intercepts, the interaction plot, a county choropleth map, and an exploratory scatter tool.

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
   jupyter notebook notebooks/04_multilevel_models.ipynb
   ```

The first notebook downloads all raw data (~50 MB total). The second merges everything into `data/processed/county_swing_dataset.csv`. The third produces figures and a baseline OLS regression. The fourth fits multilevel models and saves pre-computed outputs for the dashboard.

## Project structure

```
app.py                 Streamlit dashboard
data/raw/              Raw downloaded files (not tracked in git)
data/processed/        Merged analysis-ready CSV + model outputs
notebooks/             Numbered notebooks for each pipeline step
src/                   Download and cleaning functions
figures/               Output plots
scripts/               Build scripts for notebook generation
```

## Notes

- Alaska is flagged but kept in the dataset. Its boroughs use a different reporting structure than standard counties, so most models should exclude it.
- Connecticut reorganized its counties in 2022. Some counties may not merge cleanly with the 2023 ACS data.
- Virginia independent cities are county-equivalents with their own FIPS codes and work fine in the merge.
