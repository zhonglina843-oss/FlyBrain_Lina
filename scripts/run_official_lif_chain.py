#!/usr/bin/env python3
"""Run one traceable LC4+LPLC2 -> DNp01 experiment with the official model.

Custom work: select inputs and extract an induced one-hop graph from the
official v783 tables. Dynamics: unchanged philshiu/Drosophila_brain_model
model.py (Brian2 LIF, Poisson input, synapses, delays, and spike monitor).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from brian2 import Hz, ms


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "external" / "official" / "drosophila-brain-model"
CANDIDATES = ROOT / "data" / "processed" / "official_flywire_looming_candidate_cells.csv"
OUT = ROOT / "outputs" / "official_lif_chain"
N_PER_TYPE = 5
DURATION_MS = 100.0
INPUT_RATE_HZ = 150.0


def load_official_tables():
    comp = pd.read_csv(MODEL_DIR / "Completeness_783.csv", index_col=0)
    comp.index = comp.index.astype("int64")
    edges = pd.read_parquet(MODEL_DIR / "Connectivity_783.parquet")
    candidates = pd.read_csv(CANDIDATES)
    candidates["root_id"] = candidates.root_id.astype("int64")
    return comp, edges, candidates


def choose_inputs(edges: pd.DataFrame, candidates: pd.DataFrame):
    source = candidates[candidates.cell_type.isin(["LC4", "LPLC2"])].copy()
    target = candidates[candidates.cell_type.eq("DNp01")].copy()
    direct = edges[
        edges.Presynaptic_ID.isin(source.root_id)
        & edges.Postsynaptic_ID.isin(target.root_id)
    ].copy()
    direct = direct.merge(
        source[["root_id", "cell_type", "side"]],
        left_on="Presynaptic_ID",
        right_on="root_id",
        how="left",
    ).rename(columns={"cell_type": "Presynaptic_Type", "side": "Presynaptic_Side"})
    direct = direct.merge(
        target[["root_id", "side"]],
        left_on="Postsynaptic_ID",
        right_on="root_id",
        how="left",
        suffixes=("", "_target"),
    ).rename(columns={"side": "Postsynaptic_Side"})
    direct = direct.drop(columns=[c for c in ("root_id", "root_id_target") if c in direct.columns])
    if direct.empty:
        raise SystemExit("No direct LC4/LPLC2 -> DNp01 edges in official Connectivity_783.parquet")

    strength = (
        direct.groupby(["Presynaptic_Type", "Presynaptic_ID"], as_index=False)
        .Connectivity.sum()
        .sort_values(["Presynaptic_Type", "Connectivity"], ascending=[True, False])
    )
    selected = (
        strength.groupby("Presynaptic_Type", group_keys=False)
        .head(N_PER_TYPE)
        .reset_index(drop=True)
    )
    counts = selected.groupby("Presynaptic_Type").size().to_dict()
    if any(counts.get(t, 0) != N_PER_TYPE for t in ("LC4", "LPLC2")):
        raise SystemExit(f"Need {N_PER_TYPE} directly connected cells per type, got {counts}")
    return direct.sort_values("Connectivity", ascending=False), selected


def extract_one_hop(comp, edges, selected_ids):
    selected_ids = set(int(x) for x in selected_ids)
    outgoing = edges[edges.Presynaptic_ID.isin(selected_ids)]
    neuron_ids = selected_ids | set(outgoing.Postsynaptic_ID.astype("int64"))
    neuron_ids &= set(comp.index)
    local_comp = comp.loc[sorted(neuron_ids)].copy()
    old_index = pd.Series(range(len(comp)), index=comp.index)
    selected_old_indices = old_index.loc[local_comp.index].tolist()
    local_edges = edges[
        edges.Presynaptic_Index.isin(selected_old_indices)
        & edges.Postsynaptic_Index.isin(selected_old_indices)
    ].copy()
    old_to_new = {old: new for new, old in enumerate(selected_old_indices)}
    local_edges["Presynaptic_Index"] = local_edges.Presynaptic_Index.map(old_to_new)
    local_edges["Postsynaptic_Index"] = local_edges.Postsynaptic_Index.map(old_to_new)
    return local_comp, local_edges


def main():
    sys.path.insert(0, str(MODEL_DIR))
    import model

    comp, edges, candidates = load_official_tables()
    direct, selected = choose_inputs(edges, candidates)
    selected_ids = selected.Presynaptic_ID.astype("int64").tolist()
    dnp_ids = candidates.loc[candidates.cell_type.eq("DNp01"), "root_id"].astype("int64").tolist()
    local_comp, local_edges = extract_one_hop(comp, edges, selected_ids)
    missing_dnp = sorted(set(dnp_ids) - set(local_comp.index))
    if missing_dnp:
        raise SystemExit(f"Selected inputs do not reach DNp01 IDs directly: {missing_dnp}")

    tables = OUT / "tables"
    results = OUT / "results"
    tables.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    comp_path = tables / "Completeness_chain.csv"
    edge_path = tables / "Connectivity_chain.parquet"
    comp.to_csv(OUT / "official_completeness_reference.csv")
    local_comp.to_csv(comp_path)
    local_edges.to_parquet(edge_path, index=False)
    direct.to_csv(OUT / "direct_lc4_lplc2_to_dnp01_edges.csv", index=False)
    selected.to_csv(OUT / "selected_inputs.csv", index=False)

    params = model.default_params.copy()
    params.update(t_run=DURATION_MS * ms, n_run=1, r_poi=INPUT_RATE_HZ * Hz)
    model.run_exp(
        "lc4_lplc2_to_dnp01",
        selected_ids,
        results,
        comp_path,
        edge_path,
        params=params,
        n_proc=1,
        force_overwrite=True,
    )
    spikes = pd.read_parquet(results / "lc4_lplc2_to_dnp01.parquet")
    dnp_spikes = spikes[spikes.flywire_id.isin(dnp_ids)].copy()
    dnp_spikes.to_csv(OUT / "dnp01_spikes.csv", index=False)
    dnp_summary = []
    for root_id in dnp_ids:
        rows = dnp_spikes[dnp_spikes.flywire_id.eq(root_id)]
        side = candidates.loc[candidates.root_id.eq(root_id), "side"].iloc[0]
        dnp_summary.append(
            {
                "root_id": root_id,
                "side": side,
                "spike_count": int(len(rows)),
                "first_spike_seconds": float(rows.t.min()) if len(rows) else None,
            }
        )
    pd.DataFrame(dnp_summary).to_csv(OUT / "dnp01_summary.csv", index=False)
    summary = {
        "model": "philshiu/Drosophila_brain_model model.py (unchanged dynamics)",
        "dataset": "official FlyWire FAFB v783 tables bundled by the model authors",
        "input": {"LC4": N_PER_TYPE, "LPLC2": N_PER_TYPE, "rate_hz": INPUT_RATE_HZ},
        "duration_ms": DURATION_MS,
        "local_neurons": int(len(local_comp)),
        "local_edges": int(len(local_edges)),
        "direct_candidate_edges": int(len(direct)),
        "network_spike_rows": int(len(spikes)),
        "network_active_neurons": int(spikes.flywire_id.nunique()) if len(spikes) else 0,
        "dnp01": dnp_summary,
        "scope": "Artificial optogenetic-style activation; not a visual or behavioral simulation.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

