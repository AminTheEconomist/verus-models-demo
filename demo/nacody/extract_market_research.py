#!/usr/bin/env python3
"""
extract_market_research.py — NACody text-mining demo: pull structured fields
out of appraisal-report PDFs with pdfplumber + regex.

A cleaned, function-per-field reconstruction of the extraction logic in the
original notebooks (the first pass was a coworker's; the iterations that
followed were mine): workfile code, publication date,
customer/client, item title -> year/make/model, serial number, FMV/OLV
ranges, condition, spec bullets, and the market-research comparables that
feed the dashboard's comps section.

Runs only on the synthetic PDFs from make_sample_reports.py.

Usage:  python3 extract_market_research.py [pdf_dir] [out_csv]
"""
import csv
import re
import sys
from pathlib import Path

import pdfplumber

MAX_SPECS = 10
MAX_COMPS = 6


def extract_report(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        raw = "\n".join(p.extract_text() or "" for p in pdf.pages)
    flat = re.sub(r"\s+", " ", raw)
    row = {"SourceFile": pdf_path.name}

    def grab(field, pattern, text=raw, group=1):
        m = re.search(pattern, text)
        row[field] = m.group(group).strip() if m else ""

    # Header block (same anchors as the original notebooks)
    grab("Workfile", r"([A-Z]{5}\d{10})")
    grab("PublishedDate", r"Publication Date:\s*(.+)")
    grab("PublishedYear", r"Publication Date:.*?(\d{4})")
    grab("Customer", r"Customer\s*:\s*(.+)")
    grab("Client", r"Attention\s+([A-Za-z][A-Za-z .'-]+)")

    # Asset block: item title decomposed into year/make/model
    grab("Item", r"Item\s*:\s*(.+?)\s*Serial Number", flat)
    grab("SerialNumber", r"Serial Number\s*:\s*(\S{6,20})", flat)
    if row.get("Item"):
        m = re.match(r"(\d{4})\s+(\S+)\s+(\S+)\s+(.*)", row["Item"])
        if m:
            row["AssetYear"], row["AssetMake"] = m.group(1), m.group(2)
            row["AssetModel"], row["AssetType"] = m.group(3), m.group(4)

    # Value ranges
    grab("FMV_Low",  r"Fair Market Value \(FMV\)\s*:\s*\$([\d,]+)", flat)
    grab("FMV_High", r"Fair Market Value \(FMV\)\s*:\s*\$[\d,]+\s*-\s*\$([\d,]+)", flat)
    grab("OLV_Low",  r"Orderly Liquidation Value \(OLV\)\s*:\s*\$([\d,]+)", flat)
    grab("OLV_High", r"Orderly Liquidation Value \(OLV\)\s*:\s*\$[\d,]+\s*-\s*\$([\d,]+)", flat)

    # Condition keyword (good/fair/poor/bad ... condition)
    grab("Condition", r"(good|bad|fair|poor)(?:.{0,15})condition", flat)

    # Spec bullets
    specs = re.findall(r"(?:•|\x95)\s+(.+)", raw)
    for i in range(MAX_SPECS):
        row[f"Spec{i+1}"] = specs[i].strip() if i < len(specs) else ""
    row["NumSpecs"] = len(specs)

    # Market research comparables
    comps = re.findall(r"\[(Dealer|Auction|Ad)\]\s+(.+)", raw)
    for i in range(MAX_COMPS):
        row[f"CompType{i+1}"] = comps[i][0] if i < len(comps) else ""
        row[f"CompText{i+1}"] = comps[i][1].strip() if i < len(comps) else ""
    row["NumComps"] = len(comps)
    return row


def main():
    pdf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sample_reports"
    out_csv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "extracted_assets.csv"

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs in {pdf_dir} - run make_sample_reports.py first.")

    rows = [extract_report(p) for p in pdfs]
    cols = list(rows[0].keys())
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"Extracted {len(rows)} reports -> {out_csv}")
    for r in rows:
        print(f"  {r['Workfile']}: {r['Item']} | FMV ${r['FMV_Low']}-${r['FMV_High']} "
              f"| {r['NumComps']} comps, {r['NumSpecs']} specs")


if __name__ == "__main__":
    main()
