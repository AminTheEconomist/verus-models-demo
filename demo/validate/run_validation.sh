#!/bin/bash
# run_validation.sh — End-to-end harness for the Verus models demo.
# Proves the whole pipeline runs cold and the models recover known parameters.
#
#   1. Generate synthetic asset data (known ground truth)
#   2. R: fit depreciation models, export coefficients + rates  (DeprRateAnalyzR)
#   3. Generate synthetic appraisal PDFs
#   4. Text-mine the PDFs                                        (NACody)
#   5. Build the Excel dashboard from R output + extracted comps
#   6. Assert everything against ground truth
#
# Requires: python3 (pandas/openpyxl/pdfplumber), Rscript (dplyr).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "--- [1/6] Synthetic data"
python3 data/make_synthetic_data.py data

echo "--- [2/6] DeprRateAnalyzR (R models)"
(cd deprrate && Rscript depr_rate_analyzer.R ../data/assets_demo.csv output)

echo "--- [3/6] Sample appraisal PDFs"
python3 nacody/make_sample_reports.py

echo "--- [4/6] NACody extraction"
python3 nacody/extract_market_research.py

echo "--- [5/6] Dashboard build"
python3 nacody/build_dashboard.py

echo "--- [6/6] Validation checks"
python3 validate/check_results.py
