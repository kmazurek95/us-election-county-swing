"""Build notebook 04 as JSON. Run from project root."""
import json
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

cells = []


def md(s):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [s]})


def code(s):
    lines = s.split("\n")
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in lines[:-1]] + [lines[-1]]
    })


# ---- NOTEBOOK CELLS ----

md(
    "# 04 - Multilevel Models\n\n"
    "The OLS in notebook 03 treats all 3,100 counties as independent observations, "
    "ignoring that counties are nested within states. A multilevel model accounts for "
    "this clustering and lets us ask: how much of the swing variation is between states "
    "vs. within states? And does the education-swing relationship vary across states?"
)

code(
    'import pandas as pd\n'
    'import numpy as np\n'
    'import matplotlib.pyplot as plt\n'
    'import seaborn as sns\n'
    'import statsmodels.formula.api as smf\n'
    'from scipy import stats\n'
    '\n'
    'plt.rcParams["figure.dpi"] = 100\n'
    'sns.set_style("whitegrid")\n'
    '\n'
    'df = pd.read_csv("../data/processed/county_swing_dataset.csv",\n'
    '                 dtype={"FIPS": str, "state_fips": str})\n'
    'df_main = df[~df["is_alaska"]].copy()\n'
    'print(f"Counties in analysis: {len(df_main)}")'
)

md("## Data preparation")

code(
    '# Grand-mean center the key predictors\n'
    'df_main["college_c"] = df_main["pct_college"] - df_main["pct_college"].mean()\n'
    'df_main["unemp_change_c"] = df_main["unemp_rate_change"] - df_main["unemp_rate_change"].mean()\n'
    '\n'
    '# Drop rows missing any model variable, cast urban_rural_code\n'
    'model_vars = ["swing", "state_fips", "college_c", "pct_hispanic", "log_pop_density",\n'
    '              "rep_share_2020", "pct_black", "log_median_income", "urban_rural_code",\n'
    '              "unemp_change_c"]\n'
    'mlm_df = df_main.dropna(subset=model_vars).copy()\n'
    'mlm_df["urban_rural_code"] = mlm_df["urban_rural_code"].astype(int)\n'
    '\n'
    'print(f"Observations for modeling: {len(mlm_df)}")\n'
    'print(f"States: {mlm_df.state_fips.nunique()}")\n'
    'print(f"College pct mean: {df_main.pct_college.mean()*100:.1f}% (centering target)")\n'
    'print(f"Unemp change mean: {df_main.unemp_rate_change.mean():.2f} pp (centering target)")'
)

md("## Step 1: Null model (ICC)\n\nHow much of the county-level swing variance sits at the state level?")

code(
    'm0 = smf.mixedlm("swing ~ 1", data=mlm_df, groups=mlm_df["state_fips"])\n'
    'm0_fit = m0.fit(method="powell", reml=False)\n'
    'print(m0_fit.summary())\n'
    '\n'
    '# ICC = state variance / (state variance + residual variance)\n'
    'var_state = m0_fit.cov_re.iloc[0, 0]\n'
    'var_resid = m0_fit.scale\n'
    'icc = var_state / (var_state + var_resid)\n'
    '\n'
    'print(f"\\nState-level variance (tau_00): {var_state:.6f}")\n'
    'print(f"Residual variance (sigma^2):   {var_resid:.6f}")\n'
    'print(f"ICC = {icc:.4f}")\n'
    'print(f"\\n{icc*100:.1f}% of the variance in county-level partisan swing is between states.")'
)

md("## Step 2: Random intercepts + county-level predictors")

code(
    'formula = ("swing ~ college_c + pct_hispanic + log_pop_density + "\n'
    '          "rep_share_2020 + pct_black + log_median_income + "\n'
    '          "C(urban_rural_code)")\n'
    '\n'
    'm1 = smf.mixedlm(formula, data=mlm_df, groups=mlm_df["state_fips"])\n'
    'm1_fit = m1.fit(method="powell", reml=False)\n'
    'print(m1_fit.summary())\n'
    '\n'
    'lr_10 = 2 * (m1_fit.llf - m0_fit.llf)\n'
    'df_diff_10 = len(m1_fit.fe_params) - len(m0_fit.fe_params)\n'
    'p_10 = stats.chi2.sf(lr_10, df_diff_10)\n'
    'print(f"\\nLR test vs null: chi2={lr_10:.2f}, df={df_diff_10}, p={p_10:.2e}")'
)

md("## Step 3: Add random slope on education\n\nDoes the effect of college education on swing vary across states?")

code(
    'm2 = smf.mixedlm(formula, data=mlm_df,\n'
    '                 groups=mlm_df["state_fips"],\n'
    '                 re_formula="~college_c")\n'
    'm2_fit = m2.fit(method="powell", reml=False)\n'
    'print(m2_fit.summary())\n'
    '\n'
    '# LR test: m2 vs m1 (added slope variance + covariance = 2 parameters)\n'
    'lr_21 = 2 * (m2_fit.llf - m1_fit.llf)\n'
    'p_21 = stats.chi2.sf(lr_21, 2)\n'
    'print(f"\\nLR test (random slope): chi2={lr_21:.2f}, df=2, p={p_21:.2e}")\n'
    'if p_21 < 0.05:\n'
    '    print("The education effect DOES vary significantly across states.")\n'
    'else:\n'
    '    print("The education effect does NOT vary significantly across states.")'
)

md("## Step 4: Cross-level interaction\n\nDoes state-level unemployment change explain why the education effect varies?")

code(
    'formula_interact = ("swing ~ college_c * unemp_change_c + pct_hispanic + "\n'
    '                    "log_pop_density + rep_share_2020 + pct_black + "\n'
    '                    "log_median_income + C(urban_rural_code)")\n'
    '\n'
    'm3 = smf.mixedlm(formula_interact, data=mlm_df,\n'
    '                 groups=mlm_df["state_fips"],\n'
    '                 re_formula="~college_c")\n'
    'm3_fit = m3.fit(method="powell", reml=False)\n'
    'print(m3_fit.summary())\n'
    '\n'
    'lr_32 = 2 * (m3_fit.llf - m2_fit.llf)\n'
    'p_32 = stats.chi2.sf(lr_32, 2)\n'
    'interact_p = m3_fit.pvalues.get("college_c:unemp_change_c", float("nan"))\n'
    'interact_coef = m3_fit.fe_params.get("college_c:unemp_change_c", float("nan"))\n'
    'print(f"\\nInteraction coefficient: {interact_coef:.6f}")\n'
    'print(f"Interaction p-value: {interact_p:.4f}")\n'
    'print(f"LR test vs m2: chi2={lr_32:.2f}, p={p_32:.4f}")'
)

md(
    "The cross-level interaction is not significant. The education-swing relationship "
    "varies across states (Step 3 confirmed this), but state-level unemployment change "
    "does not explain that variation. What drives the state-level differences remains "
    "an open question."
)

md(
    "## Refit best model with REML for final reporting\n\n"
    "ML estimation is needed for likelihood ratio tests, but REML gives less biased "
    "variance component estimates. Refit m2 with REML for the numbers we report."
)

code(
    'm2_reml = smf.mixedlm(formula, data=mlm_df,\n'
    '                      groups=mlm_df["state_fips"],\n'
    '                      re_formula="~college_c")\n'
    'm2_reml_fit = m2_reml.fit(method="powell")  # default is REML\n'
    'print(m2_reml_fit.summary())'
)

md("## Model comparison table")

code(
    'rows = []\n'
    'for name, fit in [("m0_null", m0_fit), ("m1_random_intercept", m1_fit),\n'
    '                   ("m2_random_slope", m2_fit), ("m3_interaction", m3_fit)]:\n'
    '    rows.append({\n'
    '        "model": name,\n'
    '        "log_likelihood": round(fit.llf, 2),\n'
    '        "n_fixed_effects": len(fit.fe_params),\n'
    '    })\n'
    '\n'
    'comp_df = pd.DataFrame(rows)\n'
    'comp_df.to_csv("../data/processed/model_comparison.csv", index=False)\n'
    'print(comp_df.to_string(index=False))'
)

md("## Extract and save random effects (BLUPs)\n\nAll saved outputs come from the REML fit (m2_reml_fit).")

code(
    'sample_re = list(m2_reml_fit.random_effects.values())[0]\n'
    'print(f"Random effects keys: {list(sample_re.index)}")\n'
    '\n'
    're_rows = []\n'
    'for state, effects in m2_reml_fit.random_effects.items():\n'
    '    re_rows.append({\n'
    '        "state_fips": state,\n'
    '        "intercept_re": effects.iloc[0],\n'
    '        "slope_college_re": effects.iloc[1] if len(effects) > 1 else 0.0,\n'
    '    })\n'
    'state_re = pd.DataFrame(re_rows)\n'
    '\n'
    'try:\n'
    '    from us import states as us_states\n'
    '    fips_to_name = {s.fips: s.name for s in us_states.STATES_AND_TERRITORIES}\n'
    '    fips_to_abbr = {s.fips: s.abbr for s in us_states.STATES_AND_TERRITORIES}\n'
    '    state_re["state_name"] = state_re["state_fips"].map(fips_to_name)\n'
    '    state_re["state_abbr"] = state_re["state_fips"].map(fips_to_abbr)\n'
    'except ImportError:\n'
    '    state_re["state_name"] = state_re["state_fips"]\n'
    '    state_re["state_abbr"] = state_re["state_fips"]\n'
    '\n'
    'state_re["state_name"] = state_re["state_name"].fillna(state_re["state_fips"])\n'
    'state_re["state_abbr"] = state_re["state_abbr"].fillna(state_re["state_fips"])\n'
    '\n'
    'state_re.to_csv("../data/processed/state_random_effects.csv", index=False)\n'
    'print(f"Saved {len(state_re)} state random effects")\n'
    'print(state_re.sort_values("intercept_re")[["state_name", "intercept_re", "slope_college_re"]].to_string())'
)

md("## Save fixed effects from REML fit")

code(
    'fe = pd.DataFrame({\n'
    '    "term": m2_reml_fit.fe_params.index,\n'
    '    "estimate": m2_reml_fit.fe_params.values,\n'
    '    "std_err": m2_reml_fit.bse.values,\n'
    '    "z": m2_reml_fit.tvalues.values,\n'
    '    "p_value": m2_reml_fit.pvalues.values,\n'
    '})\n'
    'fe.to_csv("../data/processed/fixed_effects.csv", index=False)\n'
    'print(fe.to_string(index=False))'
)

md("## Save interaction predictions")

code(
    'college_range = np.linspace(mlm_df["college_c"].min(), mlm_df["college_c"].max(), 100)\n'
    'unemp_sd = mlm_df["unemp_change_c"].std()\n'
    'unemp_levels = {"Mean": 0, "+1 SD": unemp_sd, "-1 SD": -unemp_sd}\n'
    '\n'
    'b = m3_fit.fe_params\n'
    'interact_key = "college_c:unemp_change_c"\n'
    '\n'
    'pred_rows = []\n'
    'for label, unemp_val in unemp_levels.items():\n'
    '    pred_swing = (b["Intercept"]\n'
    '                  + (b["college_c"] + b.get(interact_key, 0) * unemp_val) * college_range\n'
    '                  + b.get("unemp_change_c", 0) * unemp_val)\n'
    '    for c, s in zip(college_range, pred_swing):\n'
    '        pred_rows.append({\n'
    '            "college_c": c,\n'
    '            "college_pct": (c + df_main["pct_college"].mean()) * 100,\n'
    '            "unemp_level": label,\n'
    '            "predicted_swing": s,\n'
    '        })\n'
    '\n'
    'pred_df = pd.DataFrame(pred_rows)\n'
    'pred_df.to_csv("../data/processed/interaction_predictions.csv", index=False)\n'
    'print(f"Saved {len(pred_df)} prediction rows")'
)

md("## Figure 1: Caterpillar plot of state random intercepts")

code(
    'state_sorted = state_re.sort_values("intercept_re")\n'
    '\n'
    'fig, ax = plt.subplots(figsize=(8, 14))\n'
    'y_pos = range(len(state_sorted))\n'
    'ax.scatter(state_sorted["intercept_re"] * 100, y_pos, s=25, color="#2c3e50", zorder=3)\n'
    'ax.axvline(0, color="red", linestyle="--", linewidth=0.8, alpha=0.7)\n'
    'ax.set_yticks(list(y_pos))\n'
    'ax.set_yticklabels(state_sorted["state_name"], fontsize=7)\n'
    'ax.set_xlabel("State random intercept (pp, deviation from average)")\n'
    'ax.set_title("State-level deviations in partisan swing\\n(after controlling for county demographics)")\n'
    'plt.tight_layout()\n'
    'plt.savefig("../figures/caterpillar_state_intercepts.png", dpi=150, bbox_inches="tight")\n'
    'plt.show()'
)

md("## Figure 2: Interaction plot\n\nEducation effect at different levels of state unemployment change. The near-parallel lines reflect the non-significant interaction.")

code(
    'fig, ax = plt.subplots(figsize=(8, 6))\n'
    'colors = {"Mean": "#2c3e50", "+1 SD": "#c0392b", "-1 SD": "#2980b9"}\n'
    'for label in ["Mean", "+1 SD", "-1 SD"]:\n'
    '    subset = pred_df[pred_df["unemp_level"] == label]\n'
    '    ax.plot(subset["college_pct"], subset["predicted_swing"] * 100,\n'
    '            label=f"State unemp change: {label}", color=colors[label], linewidth=2)\n'
    '\n'
    'interact_p_val = m3_fit.pvalues.get("college_c:unemp_change_c", float("nan"))\n'
    'ax.set_xlabel("% with bachelors degree")\n'
    'ax.set_ylabel("Predicted swing (pp)")\n'
    'ax.set_title(f"Education-swing relationship by state unemployment context\\n(interaction p = {interact_p_val:.3f}, not significant)")\n'
    'ax.legend()\n'
    'plt.tight_layout()\n'
    'plt.savefig("../figures/interaction_plot.png", dpi=150, bbox_inches="tight")\n'
    'plt.show()'
)

md("## Figure 3: Random slope distribution\n\nHow much does the education effect vary across states?")

code(
    'fig, ax = plt.subplots(figsize=(8, 5))\n'
    'ax.hist(state_re["slope_college_re"] * 100, bins=20, edgecolor="white", color="#5a7d9a")\n'
    'ax.axvline(0, color="red", linestyle="--", linewidth=0.8)\n'
    'mean_slope = m2_reml_fit.fe_params["college_c"] * 100\n'
    'ax.axvline(mean_slope, color="black", linestyle="-", linewidth=1,\n'
    '           label=f"Fixed effect: {mean_slope:.2f} pp")\n'
    'ax.set_xlabel("State-specific education slope (pp swing per 1pp increase in college %)")\n'
    'ax.set_ylabel("Number of states")\n'
    'ax.set_title("Variation in the education-swing relationship across states")\n'
    'ax.legend()\n'
    'plt.tight_layout()\n'
    'plt.savefig("../figures/random_slopes_histogram.png", dpi=150, bbox_inches="tight")\n'
    'plt.show()'
)

md("## Figure 4: Hispanic share with key states highlighted")

code(
    'highlight_states = {"48": "Texas", "12": "Florida", "04": "Arizona",\n'
    '                    "32": "Nevada", "06": "California"}\n'
    'plot_df = mlm_df.copy()\n'
    'plot_df["highlight"] = plot_df["state_fips"].map(highlight_states)\n'
    '\n'
    'fig, ax = plt.subplots(figsize=(10, 7))\n'
    '\n'
    'bg = plot_df[plot_df["highlight"].isna()]\n'
    'ax.scatter(bg["pct_hispanic"] * 100, bg["swing"] * 100,\n'
    '           s=np.sqrt(bg["total_pop"]) / 10, alpha=0.1, color="gray", edgecolors="none")\n'
    '\n'
    'hl_colors = {"Texas": "#e74c3c", "Florida": "#3498db", "Arizona": "#e67e22",\n'
    '             "Nevada": "#9b59b6", "California": "#27ae60"}\n'
    'for fips, name in highlight_states.items():\n'
    '    sub = plot_df[plot_df["state_fips"] == fips]\n'
    '    ax.scatter(sub["pct_hispanic"] * 100, sub["swing"] * 100,\n'
    '               s=np.sqrt(sub["total_pop"]) / 10, alpha=0.7,\n'
    '               color=hl_colors[name], label=name, edgecolors="white", linewidth=0.3)\n'
    '\n'
    'ax.set_xlabel("% Hispanic/Latino")\n'
    'ax.set_ylabel("Republican swing (pp)")\n'
    'ax.set_title("Hispanic population share and swing, key states highlighted")\n'
    'ax.legend(loc="upper right")\n'
    'plt.tight_layout()\n'
    'plt.savefig("../figures/hispanic_highlighted_states.png", dpi=150, bbox_inches="tight")\n'
    'plt.show()'
)

md(
    "## Summary\n\n"
    "The multilevel analysis reveals three key findings:\n\n"
    "1. **31% of swing variance is between states** (ICC = 0.305). State-level context matters substantially.\n"
    "2. **The education effect varies by state** (random slope LR test p < 0.001). In some states, college-educated counties resisted the Republican swing more than in others.\n"
    "3. **State unemployment change does not explain this variation** (interaction p = 0.48). Whatever drives the state-level differences in the education effect, it is not labor market conditions. This remains an open question for future work."
)

# ---- BUILD NOTEBOOK ----

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13.0"}
    },
    "cells": cells
}

with open("notebooks/04_multilevel_models.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print(f"Created notebook with {len(cells)} cells")
for i, c in enumerate(cells):
    t = c["cell_type"]
    s = "".join(c["source"])[:55]
    print(f"  {i}: [{t:8s}] {s}")
