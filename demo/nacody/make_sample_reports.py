#!/usr/bin/env python3
"""
make_sample_reports.py — Generate synthetic appraisal-report PDFs for the
NACody text-mining demo.

Every name, number, serial, and value here is invented. The page LAYOUT
mirrors the real Verus appraisal reports (workfile code, publication date,
client block, item/serial lines, FMV/OLV ranges, spec bullets, market
research comparables) so the extractor demonstrates the same regex patterns
the original scraper notebooks used — without touching client data.

Writes:  sample_reports/<WORKFILE>.pdf  (x3)
         sample_reports/ground_truth.json   (expected extraction values)

Uses a minimal hand-rolled PDF writer (no third-party PDF generation
dependency; pdfplumber reads the output fine).
"""
import json
import zlib
from pathlib import Path

OUTDIR = Path(__file__).parent / "sample_reports"

REPORTS = [
    {
        "Workfile": "DEMOA2024010001",
        "PublishedDate": "March 12, 2024",
        "Customer": "Northgate Lending Corp.",
        "Client": "Dana Whitfield",
        "Item": "2018 Demotern DT-450 Highway Tractor",
        "SerialNumber": "DMT45018X0042917",
        "FMV_Low": "78,500", "FMV_High": "86,000",
        "OLV_Low": "64,000", "OLV_High": "70,500",
        "Specs": ["612,400 km", "Engine: Demotern D15, 505 HP",
                  "18-speed manual transmission", "Tandem axle, GVWR 23,600 kg",
                  "72\" mid-rise sleeper"],
        "Condition": "good",
        "Comps": [
            ("Dealer", "2018 Demotern DT-450, 598,000 km, asking $89,900 - Westbrook Truck Sales"),
            ("Dealer", "2017 Demotern DT-450, 655,000 km, asking $81,500 - Apex Heavy Trucks"),
            ("Auction", "2018 Demotern DT-400, 640,200 km, sold $74,000 - Plains Equipment Auction, Feb 2024"),
        ],
    },
    {
        "Workfile": "DEMOB2024020002",
        "PublishedDate": "April 3, 2024",
        "Customer": "Cascade Mutual Insurance",
        "Client": "Priya Raman",
        "Item": "2015 Terraforge TX-350 Crawler Excavator",
        "SerialNumber": "TFX35015B0007731",
        "FMV_Low": "112,000", "FMV_High": "124,000",
        "OLV_Low": "92,000", "OLV_High": "101,500",
        "Specs": ["9,840 hours", "Engine: Terraforge TF-9, 268 HP",
                  "36\" triple-grouser tracks", "Hydraulic thumb and quick coupler"],
        "Condition": "fair",
        "Comps": [
            ("Dealer", "2015 Terraforge TX-350, 10,200 hrs, asking $129,000 - Granite Equipment Co."),
            ("Auction", "2014 Terraforge TX-350, 11,050 hrs, sold $98,500 - Plains Equipment Auction, Jan 2024"),
            ("Ad", "2016 Terraforge TX-350, 8,700 hrs, listed $138,000 - EquipTrader online"),
        ],
    },
    {
        "Workfile": "DEMOC2024030003",
        "PublishedDate": "May 21, 2024",
        "Customer": "Harborview Capital Bank",
        "Client": "Marcus Oduya",
        "Item": "2020 Boxline BL-53 Dry Van Trailer",
        "SerialNumber": "BXL53020T0019284",
        "FMV_Low": "34,000", "FMV_High": "38,500",
        "OLV_Low": "27,500", "OLV_High": "31,000",
        "Specs": ["53' x 102\" dry van", "Air ride suspension",
                  "Swing doors, plate interior", "Tandem axle, GVWR 30,840 kg"],
        "Condition": "good",
        "Comps": [
            ("Dealer", "2020 Boxline BL-53, asking $39,900 - Lakeside Trailer Sales"),
            ("Auction", "2019 Boxline BL-53, sold $31,200 - Plains Equipment Auction, Mar 2024"),
            ("Ad", "2021 Cargomate CM-53, listed $44,500 - EquipTrader online"),
        ],
    },
]


def pdf_escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def write_pdf(path, lines):
    """Single-page text PDF: Helvetica 10pt, one text line per list entry."""
    content = ["BT /F1 10 Tf 50 770 Td 14 TL"]
    for ln in lines:
        content.append(f"({pdf_escape(ln)}) Tj T*")
    content.append("ET")
    stream = zlib.compress("\n".join(content).encode("latin-1", "replace"))

    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                b"/Encoding /WinAnsiEncoding >>")
    objs.append(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream)
                + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, xref_pos))
    path.write_bytes(bytes(out))


def report_lines(r):
    lines = [
        "VERUS DEMO APPRAISALS  (SYNTHETIC SAMPLE - NOT A REAL REPORT)",
        f"Publication Date: {r['PublishedDate']}",
        f"Workfile : {r['Workfile']}",
        "",
        f"Customer : {r['Customer']}",
        f"Attention  {r['Client']}",
        "",
        f"Item : {r['Item']} Serial Number : {r['SerialNumber']}",
        "",
        "We have appraised the asset described above based on a desktop review.",
        f"The asset was found to be in {r['Condition']} condition overall.",
        "",
        f"Fair Market Value (FMV) : ${r['FMV_Low']} - ${r['FMV_High']}",
        f"Orderly Liquidation Value (OLV) : ${r['OLV_Low']} - ${r['OLV_High']}",
        "",
        "Specifications:",
    ]
    for s in r["Specs"]:
        lines.append(f"    \x95     {s}")  # \x95 = bullet in latin-1
    lines += ["", "Market Research:"]
    for kind, text in r["Comps"]:
        lines.append(f"  [{kind}] {text}")
    return lines


def main():
    OUTDIR.mkdir(exist_ok=True)
    truth = {}
    for r in REPORTS:
        path = OUTDIR / f"{r['Workfile']}.pdf"
        write_pdf(path, report_lines(r))
        truth[r["Workfile"]] = {
            "PublishedDate": r["PublishedDate"],
            "PublishedYear": r["PublishedDate"].split()[-1],
            "Customer": r["Customer"],
            "Client": r["Client"],
            "Item": r["Item"],
            "SerialNumber": r["SerialNumber"],
            "FMV_Low": r["FMV_Low"], "FMV_High": r["FMV_High"],
            "OLV_Low": r["OLV_Low"], "OLV_High": r["OLV_High"],
            "Condition": r["Condition"],
            "NumSpecs": len(r["Specs"]),
            "NumComps": len(r["Comps"]),
        }
        print(f"Wrote {path.name}")
    with open(OUTDIR / "ground_truth.json", "w") as f:
        json.dump(truth, f, indent=2)
    print(f"Wrote ground_truth.json ({len(truth)} reports)")


if __name__ == "__main__":
    main()
