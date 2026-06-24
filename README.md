# Verus Models Demo — NACody & DeprRateAnalyzR (sanitized)

Interview-ready reconstruction of two internal tools built at Verus Valuations
(Nov 2022 – Apr 2024). **Everything in `demo/` is synthetic** — no client
names, appraisal values, or serials from the real work appear anywhere here.

## Run it

```bash
bash demo/validate/run_validation.sh
```

~15 seconds: generates synthetic data → fits the R models → makes sample
appraisal PDFs → text-mines them → builds the Excel dashboard → asserts ~75
checks, ending in `ALL CHECKS PASSED`.

## The 5-minute interview walkthrough

1. **Open `demo/nacody/NACody_Demo_Dashboard.xlsx` → Estimator sheet.**
   "At Verus I fitted log-linear depreciation models in R per asset class —
   age, usage meter, replacement cost, title status — and exported the
   coefficients into Excel so appraisers could price an asset live."
   Change Age 6 → 10 and watch the FMV band drop. The formulas are visible:
   VLOOKUP into Model_Params, exactly the pattern of the real RegResults.xlsx.

2. **Show `Depr_Rates` sheet.** "The same models give the annual depreciation
   rate per class — 1 − e^(age coefficient): ~12.6%/yr for highway tractors,
   ~9%/yr for trailers. Those rates went into the depreciation section of
   collateral appraisal reports for banks and insurers."

3. **Show `Market_Comps` sheet, then a PDF in `demo/nacody/sample_reports/`.**
   "The market-research section was fed by a text-mining pipeline — pdfplumber
   plus regex over historical appraisal PDFs, pulling out dealer ads, auction
   results, specs, and the appraised value ranges."

4. **Show `demo/deprrate/depr_rate_analyzer.R`.** "This is the modeling
   pipeline — the cleaning rules and model specs are the ones from my actual
   R history at Verus." (The real `.Rhistory` exists and proves it.)

5. **The closer — run the harness live.** "Because I can't show client data,
   I validate the demo differently: the synthetic data is generated from known
   parameters, and the test suite proves the pipeline *recovers* them — the
   age coefficient, the usage effect, the rebuilt-title discount, the logit.
   That's a stronger claim than 'it runs'."

## Honesty notes (truth-first)

- The surviving Verus code is **linear** (log-linear lm, incl. title-status
  interaction models). No logit code survives on disk. The logit in this demo
  (P(rebuilt title) ~ age + usage) is a formalization of the title-status work
  stream — say so if asked, or soften the resume bullet to "linear/interaction
  models".
- The original NACody Excel workbook (with its OLE links) was not recoverable;
  this demo reconstructs its function from the surviving components.

## Layout

```
demo/
  data/      make_synthetic_data.py     synthetic asset master + ground truth
  deprrate/  depr_rate_analyzer.R       R pipeline -> output/ (coeffs, rates, logit)
  nacody/    make_sample_reports.py     synthetic appraisal PDFs
             extract_market_research.py pdfplumber+regex extraction
             build_dashboard.py         -> NACody_Demo_Dashboard.xlsx
  validate/  run_validation.sh          end-to-end harness
             check_results.py           ~75 assertions vs ground truth
```
