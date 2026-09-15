#!/usr/bin/env python3
"""Query official FlyWire synapses from LC4/LPLC2 to DNp01 via CAVEclient.

Set FLYWIRE_CAVE_TOKEN in the shell. The script reads the pinned annotation
release already recorded in data/processed and writes only small aggregate CSVs.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT = PROJECT_DIR / "data" / "processed" / "official_flywire_looming_candidate_cells.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
DATASTACK = "flywire_fafb_public"
SYNAPSE_VIEW = "valid_synapses_nt_np_v6"
SOURCE_TYPES = {"LC4", "LPLC2"}
TARGET_TYPE = "DNp01"


def main() -> None:
    token = os.environ.get("FLYWIRE_CAVE_TOKEN")
    if not token:
        raise SystemExit(
            "Missing FLYWIRE_CAVE_TOKEN. Log in at "
            "https://prod.flywire-daf.com/materialize/views/datastack/flywire_fafb_public "
            "and create a personal CAVE token. Export it only in the server shell."
        )
    if not INPUT.exists():
        raise SystemExit(f"Missing candidate metadata: {INPUT}")

    try:
        from caveclient import CAVEclient
    except ImportError as exc:
        raise SystemExit(
            "caveclient is missing. Install requirements-flywire-cave.txt first."
        ) from exc

    candidates = pd.read_csv(INPUT, dtype={"root_id": "int64"})
    source = candidates[candidates.cell_type.isin(SOURCE_TYPES)]
    target = candidates[candidates.cell_type.eq(TARGET_TYPE)]
    if source.empty or target.empty:
        raise SystemExit("Candidate metadata does not contain expected LC4/LPLC2/DNp01 rows.")

    client = CAVEclient(DATASTACK, auth_token=token)
    synapses = client.materialize.query_view(
        SYNAPSE_VIEW,
        filter_in_dict={
            "pre_pt_root_id": source.root_id.astype("int64").tolist(),
            "post_pt_root_id": target.root_id.astype("int64").tolist(),
        },
    )

    if synapses.empty:
        raise SystemExit(
            "The query returned no direct synapses. Record this result with the "
            "materialization version and verify the selected root IDs in Codex."
        )

    source_labels = source.set_index("root_id").cell_type.rename("pre_type")
    target_labels = target.set_index("root_id").cell_type.rename("post_type")
    synapses = synapses.assign(
        pre_type=synapses.pre_pt_root_id.map(source_labels),
        post_type=synapses.post_pt_root_id.map(target_labels),
    )
    group_columns = ["pre_type", "pre_pt_root_id", "post_type", "post_pt_root_id"]
    if "neuropil" in synapses.columns:
        group_columns.append("neuropil")
    summary = (
        synapses.groupby(group_columns, dropna=False)
        .size()
        .rename("synapse_count")
        .reset_index()
        .sort_values("synapse_count", ascending=False)
    )
    type_summary = (
        summary.groupby(["pre_type", "post_type"], dropna=False)
        .synapse_count.sum()
        .rename("synapse_count")
        .reset_index()
        .sort_values("synapse_count", ascending=False)
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    edges_path = OUTPUT_DIR / "flywire_lc4_lplc2_to_dnp01_edges.csv"
    types_path = OUTPUT_DIR / "flywire_lc4_lplc2_to_dnp01_type_summary.csv"
    summary.to_csv(edges_path, index=False)
    type_summary.to_csv(types_path, index=False)
    print(f"Retrieved {len(synapses):,} synapses from {DATASTACK}/{SYNAPSE_VIEW}.")
    print(f"Wrote {edges_path}")
    print(f"Wrote {types_path}")
    print(f"Query date: {date.today().isoformat()}")
    print(f"Materialization version requested: latest ({max(client.materialize.get_versions())})")


if __name__ == "__main__":
    main()
