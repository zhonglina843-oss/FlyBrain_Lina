#!/usr/bin/env python3
"""Run the official Brian2 model on a small downstream connectome subgraph.

The neuron equations and simulation call remain in the official model.py. This
script only reduces the graph before Brian2 constructs its NeuronGroup/Synapses,
which makes the official dynamics inspectable on a workstation/server.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from brian2 import Hz, ms


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "external" / "official" / "drosophila-brain-model"
CANDIDATES = ROOT / "data" / "processed" / "official_flywire_looming_candidate_cells.csv"
OUT = ROOT / "outputs" / "official_lif_local_subgraph"


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--hops", type=int, default=2)
    p.add_argument("--duration-ms", type=float, default=100.0)
    p.add_argument("--input-rate-hz", type=float, default=150.0)
    p.add_argument("--n-input", type=int, default=5)
    p.add_argument("--source-type", choices=("LC4", "LPLC2", "both"), default="both")
    p.add_argument("--label", default="lc4_lpl2_local")
    return p.parse_args()


def make_subgraph(hops: int, source_type: str):
    comp = pd.read_csv(MODEL_DIR / "Completeness_783.csv", index_col=0)
    edges = pd.read_parquet(
        MODEL_DIR / "Connectivity_783.parquet",
        columns=[
            "Presynaptic_ID",
            "Postsynaptic_ID",
            "Presynaptic_Index",
            "Postsynaptic_Index",
            "Connectivity",
            "Excitatory",
            "Excitatory x Connectivity",
        ],
    )
    candidate = pd.read_csv(CANDIDATES)
    source_types = ["LC4", "LPLC2"] if source_type == "both" else [source_type]
    seeds = candidate.loc[candidate.cell_type.isin(source_types), "root_id"].astype("int64")
    targets = candidate.loc[candidate.cell_type.eq("DNp01"), "root_id"].astype("int64")
    id_to_idx = pd.Series(range(len(comp)), index=comp.index.astype("int64"))
    frontier = set(id_to_idx.loc[id_to_idx.index.intersection(seeds)].tolist())
    target_idx = set(id_to_idx.loc[id_to_idx.index.intersection(targets)].tolist())
    selected = set(frontier)
    reached = set(frontier) & target_idx
    layer_sizes = [len(frontier)]
    for _ in range(hops):
        layer = edges[edges.Presynaptic_Index.isin(frontier)]
        nxt = set(layer.Postsynaptic_Index.astype("int64")) - selected
        selected.update(nxt)
        reached.update(nxt & target_idx)
        frontier = nxt
        layer_sizes.append(len(frontier))
        if not frontier:
            break
    selected_idx = sorted(selected)
    selected_edges = edges[
        edges.Presynaptic_Index.isin(selected)
        & edges.Postsynaptic_Index.isin(selected)
    ].copy()
    old_to_new = {old: new for new, old in enumerate(selected_idx)}
    selected_edges["Presynaptic_Index"] = selected_edges.Presynaptic_Index.map(old_to_new)
    selected_edges["Postsynaptic_Index"] = selected_edges.Postsynaptic_Index.map(old_to_new)
    selected_comp = comp.iloc[selected_idx].copy()
    selected_comp.index = [comp.index[i] for i in selected_idx]
    return selected_comp, selected_edges, seeds.tolist(), targets.tolist(), layer_sizes, reached


def main():
    cfg = args()
    sys.path.insert(0, str(MODEL_DIR))
    import model

    comp, edges, seeds, targets, layer_sizes, reached = make_subgraph(cfg.hops, cfg.source_type)
    work = OUT / "subgraph_tables" / cfg.label
    work.mkdir(parents=True, exist_ok=True)
    comp_path = work / "Completeness_local.csv"
    edge_path = work / "Connectivity_local.parquet"
    comp.to_csv(comp_path)
    edges.to_parquet(edge_path, index=False)

    valid_seeds = [int(x) for x in seeds if x in comp.index]
    valid_targets = [int(x) for x in targets if x in comp.index]
    params = model.default_params.copy()
    params.update(t_run=cfg.duration_ms * ms, n_run=1, r_poi=cfg.input_rate_hz * Hz)
    result_dir = OUT / "results" / cfg.label
    result_dir.mkdir(parents=True, exist_ok=True)
    model.run_exp(
        cfg.label,
        valid_seeds[: cfg.n_input],
        result_dir,
        comp_path,
        edge_path,
        params=params,
        neu_slnc=[],
        n_proc=1,
        force_overwrite=True,
    )
    spikes = pd.read_parquet(result_dir / f"{cfg.label}.parquet")
    summary = {
        "model": "official model.py via Brian2",
        "dataset": "FlyWire FAFB v783",
        "hops": cfg.hops,
        "layer_sizes": layer_sizes,
        "local_neurons": int(len(comp)),
        "local_edges": int(len(edges)),
        "seed_count": len(valid_seeds),
        "dnp01_reached_within_hops": [int(x) for x in reached],
        "spike_rows": int(len(spikes)),
        "active_neurons": int(spikes.flywire_id.nunique()) if len(spikes) else 0,
        "note": "Only graph extraction is custom; neuron dynamics and run_exp are official.",
    }
    (OUT / f"summary_{cfg.label}.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
