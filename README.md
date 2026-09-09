# Verus Models Demo — NACody & DeprRateAnalyzR

A working reconstruction of two internal tools I built as Software & Data
Analyst at Verus Valuations (Nov 2022 – Apr 2024): a depreciation-modeling
pipeline in R whose coefficients drive a live Excel estimator, and a
text-mining pipeline that pulls market-research comparables out of appraisal
PDFs.

The real system runs on bank and insurer collateral appraisals, so none of it
can be published. **Everything in `demo/` is synthetic** — no client names,
appraised values, or serial numbers appear anywhere in this repository.

## Run it

```bash
bash demo/validate/run_validation.sh
```

About 15 seconds: generates synthetic data → fits the R models → renders sample
appraisal PDFs → text-mines them → builds the Excel dashboard → runs 64
assertions, ending in `ALL CHECKS PASSED`.

## How it is validated

Synthetic data usually means a demo can only prove that it runs. This one
proves more. `make_synthetic_data.py` generates 2,900 assets from **known
parameters** and writes them to `ground_truth_params.json`; the test suite then
asserts that the pipeline **recovers** them — the age coefficient, the usage
effect, the rebuilt-title discount, the logit slope, and the annual
depreciation rates derived from them. If the modeling were wrong, recovery
would fail.

The other two assertion groups cover extraction and assembly: every header and
value field text-mined from each PDF must match ground truth exactly, and the
dashboard's `Model_Params` sheet must be numerically identical to the R output
with the estimator formula still live.

## What it produces

**DeprRateAnalyzR** — `demo/deprrate/depr_rate_analyzer.R` fits a log-linear
model per asset class (age, usage meter, log replacement cost, title status),
plus a binomial GLM for title status, and exports coefficients and rates as
CSV. The cleaning rules and model specifications follow the ones I used at
Verus. Annual depreciation rates come out of the age coefficient as 1 − e^β:

| Asset class | n | Annual depreciation | Usage term | Adj. R² |
|---|---|---|---|---|
| Highway Tractor | 1,173 | 12.3% | Km / 100,000 | 0.968 |
| Crawler Excavator | 900 | 11.1% | Hours / 1,000 | 0.952 |
| Dry Van Trailer | 800 | 9.0% | none (no meter) | 0.916 |

**NACody** — `extract_market_research.py` reads the sample appraisal PDFs with
pdfplumber and regex anchors, recovering workfile ID, client, year/make/model,
serial, FMV and OLV ranges, condition, spec bullets, and dealer/auction/ad
comparables. `build_dashboard.py` assembles those plus the R coefficients into
`NACody_Demo_Dashboard.xlsx`, whose Estimator sheet prices an asset live
through visible VLOOKUP formulas against `Model_Params` — the pattern the
production workbook used.

## Scope and provenance

- The demo is a reconstruction, not a copy. The original NACody workbook
  depended on OLE links into the Verus environment and could not be rebuilt
  from the surviving components; this version reproduces its function.
- The depreciation models that survive from the production work are linear —
  log-linear `lm`, including title-status interaction models. The logit here,
  P(rebuilt title) ~ age + usage, formalizes that title-status work stream
  rather than reproducing a specific model from it.
- The Excel → R → Excel loop was originally driven by VBA that shelled out to
  `Rscript` and imported the results back as a dated sheet. Here Python builds
  the workbook from the R output instead, so the demo runs on any machine.

## Layout

```
demo/
  data/      make_synthetic_data.py     synthetic asset master + ground truth
  deprrate/  depr_rate_analyzer.R       R pipeline -> output/ (coeffs, rates, logit)
  nacody/    make_sample_reports.py     synthetic appraisal PDFs
             extract_market_research.py pdfplumber + regex extraction
             build_dashboard.py         -> NACody_Demo_Dashboard.xlsx
  validate/  run_validation.sh          end-to-end harness
             check_results.py           64 assertions vs ground truth
```

Requires Python 3 with pandas, openpyxl and pdfplumber, and Rscript with dplyr.
