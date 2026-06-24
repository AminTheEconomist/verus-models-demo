#!/usr/bin/env python3
"""
make_synthetic_data.py — Generate a fully synthetic asset dataset for the
Verus models demo.

100% fake data. No client records, appraisal values, names, or serial
numbers from Verus Valuations appear here. The schema mirrors the real
Asset-Master export (CRM_Name, Year, Age, Make, Model, Category,
Sub_Category, Market_Area, FMV, NRC, Hours, Km, Engine_HP, Title_Status)
so the downstream R pipeline runs unchanged in shape.

Ground-truth generating process (written to ground_truth_params.json so the
validation harness can assert the models recover it):

    log(FMV) = b0 + b_lognrc*log(NRC) + b_age*Age + b_usage*UsageScaled
               + b_rebuilt*Rebuilt + N(0, sigma)

    P(Rebuilt) = logistic(g0 + g_age*Age + g_usage*UsageScaled)   [trucks only]

Usage:  python3 make_synthetic_data.py [outdir]
"""
import json
import math
import random
import sys
from pathlib import Path

SEED = 20260611

# Per-category ground truth. usage_col is the meter that drives depreciation;
# usage_scale converts the raw meter to model units (Km/100k, Hours/1000).
CATEGORIES = {
    "Highway Tractor": dict(
        n=1200, b0=0.55, b_lognrc=0.92, b_age=-0.135, b_usage=-0.018,
        b_rebuilt=-0.42, sigma=0.16, usage_col="Km", usage_scale=100_000,
        usage_per_year=(60_000, 130_000), nrc_range=(150_000, 260_000),
        makes=[("Demotern", ["DT-400", "DT-450"]), ("Roadcrest", ["RC-9", "RC-12"]),
               ("Vanguard Hauler", ["VH-300"])],
        hp_range=(400, 605), logit=dict(g0=-3.0, g_age=0.22, g_usage=0.9),
    ),
    "Crawler Excavator": dict(
        n=900, b0=0.40, b_lognrc=0.94, b_age=-0.115, b_usage=-0.025,
        b_rebuilt=0.0, sigma=0.18, usage_col="Hours", usage_scale=1_000,
        usage_per_year=(700, 1_600), nrc_range=(180_000, 420_000),
        makes=[("Terraforge", ["TX-210", "TX-350"]), ("Gradient", ["G-25", "G-36"])],
        hp_range=(120, 320), logit=None,
    ),
    "Dry Van Trailer": dict(
        n=800, b0=0.70, b_lognrc=0.90, b_age=-0.095, b_usage=0.0,
        b_rebuilt=0.0, sigma=0.14, usage_col=None, usage_scale=1,
        usage_per_year=(0, 0), nrc_range=(45_000, 80_000),
        makes=[("Boxline", ["BL-53", "BL-48"]), ("Cargomate", ["CM-53"])],
        hp_range=None, logit=None,
    ),
}

MARKET_AREAS = ["Western Canada", "Prairies", "Central Canada", "US Pacific NW"]
REPORT_YEAR = 2024


def gen_category(rng, name, p, start_id):
    rows = []
    for i in range(p["n"]):
        age = round(rng.uniform(0.5, 18.0), 1)
        year = REPORT_YEAR - int(age)
        make, models = rng.choice(p["makes"])
        model = rng.choice(models)
        nrc = rng.uniform(*p["nrc_range"])
        usage_raw = 0.0
        if p["usage_col"]:
            per_year = rng.uniform(*p["usage_per_year"])
            usage_raw = max(0.0, per_year * age * rng.uniform(0.8, 1.2))
        usage_scaled = usage_raw / p["usage_scale"]

        rebuilt = 0
        if p["logit"]:
            g = p["logit"]
            z = g["g0"] + g["g_age"] * age + g["g_usage"] * (usage_scaled / max(age, 0.5))
            if rng.random() < 1.0 / (1.0 + math.exp(-z)):
                rebuilt = 1

        log_fmv = (p["b0"] + p["b_lognrc"] * math.log(nrc) + p["b_age"] * age
                   + p["b_usage"] * usage_scaled + p["b_rebuilt"] * rebuilt
                   + rng.gauss(0, p["sigma"]))
        fmv = math.exp(log_fmv)

        rows.append({
            "CRM_Name": f"DEMO{REPORT_YEAR}{start_id + i:06d}",
            "Report_Date": f"{REPORT_YEAR}-03-15",
            "Year": year,
            "Age": age,
            "Make": make,
            "Model": model,
            "Category": {"Highway Tractor": "Truck",
                         "Crawler Excavator": "Construction",
                         "Dry Van Trailer": "Trailers"}[name],
            "Sub_Category": name,
            "Market_Area": rng.choice(MARKET_AREAS),
            "FMV": round(fmv, 0),
            "NRC": round(nrc, 0),
            "Hours": round(usage_raw, 0) if p["usage_col"] == "Hours" else "",
            "Km": round(usage_raw, 0) if p["usage_col"] == "Km" else "",
            "Engine_HP": rng.randint(*p["hp_range"]) if p["hp_range"] else "",
            "Title_Status": "Rebuilt" if rebuilt else "Clean",
        })
    return rows


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    rng = random.Random(SEED)
    all_rows = []
    start = 1
    for name, p in CATEGORIES.items():
        all_rows += gen_category(rng, name, p, start)
        start += p["n"]

    cols = list(all_rows[0].keys())
    csv_path = outdir / "assets_demo.csv"
    with open(csv_path, "w") as f:
        f.write(",".join(cols) + "\n")
        for r in all_rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    truth = {
        name: {k: v for k, v in p.items() if k not in ("makes",)}
        for name, p in CATEGORIES.items()
    }
    with open(outdir / "ground_truth_params.json", "w") as f:
        json.dump({"seed": SEED, "report_year": REPORT_YEAR, "categories": truth}, f, indent=2)

    print(f"Wrote {len(all_rows)} synthetic assets -> {csv_path}")
    print(f"Wrote ground truth -> {outdir / 'ground_truth_params.json'}")


if __name__ == "__main__":
    main()
