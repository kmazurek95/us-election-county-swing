# US Election County-Level Swing Analysis

About 31% of the variation in how much US counties swung toward Republicans in 2024 is explained by which state they sit in, not by county demographics. That means state-level forces (media markets, campaign spending, political environment) account for nearly a third of the swing story before you look at a single demographic variable.

This project models the 2020-to-2024 county-level partisan swing across 3,101 counties in 49 states and DC, using multilevel models that decompose the swing into state-level and county-level components.

## Key findings

The average county swung +1.7 percentage points toward Republicans, but the range runs from about 7 points left to 13 points right. Three patterns stand out.

**State context explains a third of the variance.** An empty multilevel model (no predictors, just state grouping) yields an ICC of 0.305. Standard single-level regressions miss this entirely because they cannot separate state-level from county-level variation.

**Hispanic population share is the strongest predictor of rightward swing.** A 10-percentage-point higher Hispanic share predicts about 0.46 pp more Republican swing, holding education, income, density, prior partisanship, and urban-rural classification constant. This is statistically significant (p < 0.001) and consistent with the rightward shift among Latino voters documented in Pew and Catalist post-election studies. The pattern is driven by South Texas, the Florida I-4 corridor, and Southern California, but holds nationally. Important caveat: this is a county-level finding, not an individual-level one. We cannot say that individual Hispanic voters shifted right; we can say that places with more Hispanic residents swung further right.

**Education polarization is real but varies across states.** A 10-percentage-point higher college share predicts about 0.60 pp less Republican swing (p < 0.001). But the strength of this effect differs significantly across states: adding a random slope on education improves the model substantially (likelihood ratio test chi-squared = 72.4, p < 0.001). In some states the education gradient was steep; in others it was nearly flat. We tested whether state-level economic conditions (change in unemployment rate, 2020-2024) could explain that variation. They could not (interaction p = 0.48). The source of the cross-state variation remains an open question, likely involving media environment, campaign strategy, or state political culture.

**Model progression (all fit with ML for comparison):**

| Model | AIC | What it adds |
|-------|-----|-------------|
| Null (state grouping only) | -17,231 | ICC = 0.305 |
| Random intercepts + demographics | -18,506 | County-level predictors |
| Random slope on education | -18,575 | Education effect varies by state |
| Cross-level interaction | -18,572 | State economy x education (null) |

AIC drops substantially at each step until the interaction model, where it ticks up slightly (more parameters, no improvement in fit). The random slope model is the best fit.

## Interactive dashboard

**[Explore the findings interactively](https://us-election-county-swing-9ovbfe8vvncgikvc4ftgrz.streamlit.app/)** (hosted on Streamlit Community Cloud)

Includes the caterpillar plot of state random intercepts, interaction plots, a county choropleth map, and an exploratory scatter tool.

Or run locally:
```
streamlit run app.py
```

## Policy brief

A two-page brief translating these findings for campaign strategists, advocacy organizations, and political researchers is available at [`docs/policy_brief.pdf`](docs/policy_brief.pdf).

## Data sources

- **Election returns**: MIT Election Data + Science Lab (MEDSL) county presidential returns, 2000-2024. Harvard Dataverse, DOI: 10.7910/DVN/VOQCHQ.
- **Demographics**: American Community Survey 5-year estimates (2019-2023 vintage) via the Census API.
- **State unemployment**: Bureau of Labor Statistics, Local Area Unemployment Statistics (LAUS).
- **Urban-rural classification**: NCHS 2013 urban-rural scheme (6 categories).
- **Land area**: Census 2024 county gazetteer.

## Setup

If you just want to explore the findings, skip setup and use the [live dashboard](https://us-election-county-swing-9ovbfe8vvncgikvc4ftgrz.streamlit.app/) above.

To reproduce the analysis:

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
docs/                  Policy brief and build script
scripts/               Build scripts for notebook generation
```

## Notes

- Alaska is flagged but kept in the dataset. Its boroughs use a different reporting structure than standard counties, so models exclude it.
- Connecticut reorganized its counties in 2022. Some counties may not merge cleanly with the 2023 ACS data.
- Virginia independent cities are county-equivalents with their own FIPS codes and work fine in the merge.
- The ecological fallacy applies throughout: county demographic profiles predict county swing, but that does not mean the individuals matching those demographics drove the change. Survey data and voter-file analyses complement these findings at the individual level.

## Author

Built by Kaleb Mazurek. [GitHub](https://github.com/kmazurek95) | [LinkedIn](https://www.linkedin.com/in/kaleb-mazurek/)