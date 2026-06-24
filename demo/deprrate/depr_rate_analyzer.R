#!/usr/bin/env Rscript
# depr_rate_analyzer.R — DeprRateAnalyzR demo pipeline (sanitized).
#
# A cleaned, runnable reconstruction of the depreciation-modeling workflow
# preserved in the Verus .Rhistory (Work_Data/Verus Data/.Rhistory):
#   load asset master -> coerce numerics -> range filters -> log transforms ->
#   per-subcategory linear models on log(FMV) -> export coefficient tables +
#   a depreciation-rates summary for the appraisal report.
#
# Runs entirely on synthetic data (demo/data/assets_demo.csv). No client data.
#
# Provenance notes (truth-first):
#  * The log-linear lm() specifications below mirror the surviving .Rhistory
#    (LogFMV ~ Age + usage + LogNRC + effects).
#  * The logistic model of Title_Status reflects the title-status work stream
#    (AutoTax project, Title_Status tables); the surviving Verus files show
#    linear interaction models for title status, so the glm() here is the
#    demo's formalization of that analysis. See the honesty notes in README.md.

suppressPackageStartupMessages(library(dplyr))

args <- commandArgs(trailingOnly = TRUE)
data_csv <- ifelse(length(args) >= 1, args[1], "../data/assets_demo.csv")
outdir   <- ifelse(length(args) >= 2, args[2], "output")
dir.create(outdir, showWarnings = FALSE, recursive = TRUE)

# --- Data preparation (mirrors .Rhistory cleaning steps) --------------------
df <- read.csv(data_csv, stringsAsFactors = FALSE)
for (col in c("Age", "Year", "FMV", "NRC", "Km", "Hours", "Engine_HP")) {
  df[[col]] <- suppressWarnings(as.numeric(df[[col]]))
}
df[df == "" | df == "undefined" | df == "NA"] <- NA

df <- df %>% filter(0.1 <= Age & Age < 50 & FMV >= 5000 & FMV < 12e6)
df$LogFMV <- log(df$FMV)
df$LogNRC <- log(df$NRC)
df <- df[complete.cases(df$LogFMV, df$LogNRC, df$Age), ]
df$UsageAveHours <- df$Hours / df$Age   # average annual usage
df$UsageAveKm    <- df$Km / df$Age

# --- Per-subcategory linear depreciation models ------------------------------
specs <- list(
  "Highway Tractor"   = list(formula = LogFMV ~ Age + I(Km/100000) + LogNRC + Title_Status,
                             usage = "Km/100000"),
  "Crawler Excavator" = list(formula = LogFMV ~ Age + I(Hours/1000) + LogNRC,
                             usage = "Hours/1000"),
  "Dry Van Trailer"   = list(formula = LogFMV ~ Age + LogNRC,
                             usage = "none")
)

summary_lines <- c()
depr_rows <- list()

for (sub in names(specs)) {
  d <- df %>% filter(Sub_Category == sub)
  m <- lm(specs[[sub]]$formula, data = d)
  s <- summary(m)

  coefs <- as.data.frame(s$coefficients)
  coefs <- cbind(Term = rownames(coefs), coefs)
  names(coefs) <- c("Term", "Estimate", "StdError", "tValue", "pValue")
  fn <- file.path(outdir, paste0("coefficients_", gsub(" ", "_", sub), ".csv"))
  write.csv(coefs, fn, row.names = FALSE)

  beta_age <- coef(m)[["Age"]]
  annual_depr <- 1 - exp(beta_age)          # % of value lost per year of age
  usage_terms <- grep("Km/|Hours/", names(coef(m)), value = TRUE)
  beta_usage <- if (length(usage_terms)) coef(m)[[usage_terms[1]]] else NA

  depr_rows[[sub]] <- data.frame(
    Sub_Category   = sub,
    N              = nrow(d),
    AnnualDeprRate = round(annual_depr, 4),
    UsageTerm      = specs[[sub]]$usage,
    UsageBeta      = round(ifelse(is.na(beta_usage), NA, beta_usage), 5),
    AdjR2          = round(s$adj.r.squared, 4),
    ResidualSE     = round(s$sigma, 4)
  )

  summary_lines <- c(summary_lines,
    sprintf("==== %s (n=%d) ====", sub, nrow(d)),
    capture.output(print(s)), "")
}

depr <- bind_rows(depr_rows)
write.csv(depr, file.path(outdir, "depr_rates_demo.csv"), row.names = FALSE)

# --- Logistic model: P(Rebuilt title) for trucks -----------------------------
trk <- df %>% filter(Sub_Category == "Highway Tractor") %>%
  mutate(Rebuilt = as.integer(Title_Status == "Rebuilt"),
         UsageScaledPerYear = (Km / 100000) / Age)
logit <- glm(Rebuilt ~ Age + UsageScaledPerYear, data = trk, family = binomial)
ls <- summary(logit)
lc <- as.data.frame(ls$coefficients)
lc <- cbind(Term = rownames(lc), lc)
names(lc) <- c("Term", "Estimate", "StdError", "zValue", "pValue")
write.csv(lc, file.path(outdir, "logit_title_status.csv"), row.names = FALSE)
summary_lines <- c(summary_lines, "==== Logit: P(Rebuilt) | Highway Tractor ====",
                   capture.output(print(ls)))

writeLines(summary_lines, file.path(outdir, "model_summaries.txt"))

cat("DeprRateAnalyzR demo complete.\n")
cat(sprintf("Outputs in %s: %s\n", normalizePath(outdir),
            paste(list.files(outdir), collapse = ", ")))
print(depr)
