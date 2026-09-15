#!/usr/bin/env python3
"""Extract candidate-cell metadata from the pinned official FlyWire annotations."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE = (
    PROJECT_DIR
    / "external"
    / "official"
    / "flywire-annotations"
    / "supplemental_files"
    / "Supplemental_file1_neuron_annotations.tsv"
)
TARGET_TYPES = ("LC4", "LPLC2", "DNp01")
FIELDS = (
    "root_id",
    "cell_type",
    "super_class",
    "side",
    "top_nt",
    "top_nt_conf",
    "known_nt",
    "known_nt_source",
    "vfb_id",
    "fbbt_id",
)


def collect() -> list[dict[str, str]]:
    if not SOURCE.exists():
        raise SystemExit(f"Missing official annotations: {SOURCE}")
    with SOURCE.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return [
            {field: row[field] for field in FIELDS}
            for row in reader
            if row["cell_type"] in TARGET_TYPES
        ]


def main() -> None:
    rows = collect()
    counts = Counter(row["cell_type"] for row in rows)
    today = date.today().isoformat()
    output_dir = PROJECT_DIR / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "official_flywire_looming_candidate_cells.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    representatives = {
        cell_type: next(row for row in rows if row["cell_type"] == cell_type)
        for cell_type in TARGET_TYPES
    }
    markdown_path = output_dir / "official_flywire_looming_candidate_metadata.md"
    lines = [
        "---",
        "dataset: FlyWire FAFB v783 (female adult brain)",
        "annotation_source: flyconnectome/flywire_annotations v3.1.0",
        f"generated_on: {today}",
        "scope: static annotation audit; not a connectivity query",
        "---",
        "",
        "# Official Candidate Metadata",
        "",
        "This record was generated from the pinned official annotation dump. "
        "It establishes that the named cell types and representative root IDs exist in "
        "the annotation release. It does not establish direct LC4/LPLC2 -> DNp01 edges; "
        "that requires an explicit Codex/CAVE connectivity query.",
        "",
        "## Counts",
        "",
        "| Cell type | Annotated neurons |",
        "|---|---:|",
    ]
    lines.extend(f"| {cell_type} | {counts[cell_type]} |" for cell_type in TARGET_TYPES)
    lines.extend(
        [
            "",
            "## Representative cells",
            "",
            "| Type | root ID | superclass | side | predicted transmitter | known transmitter | annotation source |",
            "|---|---:|---|---|---|---|---|",
        ]
    )
    for cell_type in TARGET_TYPES:
        row = representatives[cell_type]
        known = row["known_nt"] or "not listed"
        source = row["known_nt_source"] or "not listed"
        lines.append(
            f"| {cell_type} | {row['root_id']} | {row['super_class']} | "
            f"{row['side']} | {row['top_nt']} ({row['top_nt_conf']}) | "
            f"{known} | {source} |"
        )
    lines.extend(
        [
            "",
            "## Next manual query",
            "",
            "Use Codex with dataset `FAFB v783 (CB)` to query direct partners for the "
            "representative IDs and save the returned edge weight, ROI and query URL. "
            "Do not infer physiological strength from synapse count alone.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {csv_path}")
    print(f"Wrote audit to {markdown_path}")


if __name__ == "__main__":
    main()

