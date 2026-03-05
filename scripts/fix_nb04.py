"""Batch fix notebooks 01, 03, 04 for audit issues."""
import json

# =============================================
# NOTEBOOK 04 FIXES: DC label, histogram, AIC/BIC
# =============================================
with open("notebooks/04_multilevel_models.ipynb") as f:
    nb = json.load(f)

for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])

    # Fix #1: DC label in BLUP extraction cell
    if "fips_to_name = {s.fips: s.name for s in us_states.STATES_AND_TERRITORIES}" in src:
        src = src.replace(
            "fips_to_name = {s.fips: s.name for s in us_states.STATES_AND_TERRITORIES}",
            "fips_to_name = {s.fips: s.name for s in us_states.STATES_AND_TERRITORIES}\n    fips_to_name[\"11\"] = \"District of Columbia\"",
        )
        src = src.replace(
            "fips_to_abbr = {s.fips: s.abbr for s in us_states.STATES_AND_TERRITORIES}",
            "fips_to_abbr = {s.fips: s.abbr for s in us_states.STATES_AND_TERRITORIES}\n    fips_to_abbr[\"11\"] = \"DC\"",
        )
        lines = src.split("\n")
        cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
        cell["outputs"] = []
        print(f"  Fixed DC label in nb04 cell {i}")

    # Fix #2: Histogram - plot total slopes instead of deviations
    if "ax.hist(state_re[\"slope_college_re\"] * 100" in src:
        src = src.replace(
            "ax.hist(state_re[\"slope_college_re\"] * 100, bins=20",
            "total_slopes = (m2_reml_fit.fe_params[\"college_c\"] + state_re[\"slope_college_re\"]) * 100\nax.hist(total_slopes, bins=20",
        )
        src = src.replace(
            "ax.axvline(0, color=\"red\", linestyle=\"--\", linewidth=0.8)",
            "ax.axvline(0, color=\"red\", linestyle=\"--\", linewidth=0.8, label=\"Zero (no effect)\")",
        )
        lines = src.split("\n")
        cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
        cell["outputs"] = []
        print(f"  Fixed histogram in nb04 cell {i}")

    # Fix #5: AIC/BIC in model comparison
    if "\"log_likelihood\": round(fit.llf, 2)," in src:
        src = src.replace(
            "\"log_likelihood\": round(fit.llf, 2),",
            "\"log_likelihood\": round(fit.llf, 2),\n        \"aic\": round(fit.aic, 2),\n        \"bic\": round(fit.bic, 2),",
        )
        lines = src.split("\n")
        cell["source"] = [line + "\n" for line in lines[:-1]] + [lines[-1]]
        cell["outputs"] = []
        print(f"  Fixed AIC/BIC in nb04 cell {i}")

# Clear all outputs for clean re-run
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        cell["outputs"] = []
        cell["execution_count"] = None

with open("notebooks/04_multilevel_models.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
print("Saved notebook 04")
