#!/usr/bin/env python3
"""Run the official Shiu Brian2 LIF model on an extracted local subgraph.

The dynamics are imported unchanged from external/official/drosophila-brain-model/model.py.
Only the connectome is reduced to a reproducible two-hop downstream graph so the
official CPU Brian2 implementation can run without constructing the full 15M-edge graph.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from brian2 import Hz, ms


ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "external" / "official" / "drosophila-brain-model"
CANDIDATES = ROOT / "data" / "processed" / "official_flywire_looming_candidate_cells.csv"
OUT = ROOT / "outputs" / "official_lif_subgraph"
DATA_COMP = MODEL_DIR / "Completeness_783.csv"
DATA_CONN = MODEL_DIR / "Connectivity_783.parquet"


def scan_edges(active: set[int], columns: list[str]) -> pd.DataFrame:
    parquet = pq.ParquetFile(DATA_CONN)
    pieces = []
    for batch in parquet.iter_batches(batch_size=500_000, columns=columns):
        frame = batch.to_pandas()
        keep = frame["Presynaptic_Index"].isin(active)
        if keep.any():
            pieces.append(frame.loc[keep])
    if not pieces:
        return pd.DataFrame(columns=columns)
    return pd.concat(pieces, ignore_index=True)


def extract_subgraph(seed_indices: set[int], target_indices: set[int], hops: int = 2):
    active = set(seed_indices)
    discovered = set(seed_indices) | set(target_indices)
    columns = ["Presynaptic_Index", "Postsynaptic_Index", "Excitatory x Connectivity"]
    for _ in range(hops):
        edges = scan_edges(active, columns)
        new_nodes = set(edges["Postsynaptic_Index"].astype(int).tolist())
        discovered |= new_nodes
        active = new_nodes
    all_edges = scan_edges(discovered, columns)
    all_edges = all_edges[
        all_edges["Postsynaptic_Index"].isin(discovered)
    ].copy()
    return discovered, all_edges


def remap_and_write(nodes: set[int], edges: pd.DataFrame, completeness: pd.DataFrame):
    nodes = sorted(nodes)
    old_to_new = {old: new for new, old in enumerate(nodes)}
    sub_comp = completeness.iloc[nodes].copy()
    sub_edges = edges.copy()
    sub_edges["Presynaptic_Index"] = sub_edges["Presynaptic_Index"].map(old_to_new)
    sub_edges["Postsynaptic_Index"] = sub_edges["Postsynaptic_Index"].map(old_to_new)
    sub_edges = sub_edges.dropna(subset=["Presynaptic_Index", "Postsynaptic_Index"])
    sub_edges["Presynaptic_Index"] = sub_edges["Presynaptic_Index"].astype(int)
    sub_edges["Postsynaptic_Index"] = sub_edges["Postsynaptic_Index"].astype(int)
    OUT.mkdir(parents=True, exist_ok=True)
    comp_path = OUT / "subgraph_completeness.csv"
    conn_path = OUT / "subgraph_connectivity.parquet"
    sub_comp.to_csv(comp_path)
    pq.write_table(pa.Table.from_pandas(sub_edges, preserve_index=False), conn_path)
    return comp_path, conn_path, old_to_new


def run_official_condition(name, excited, silenced, params, comp_path, conn_path):
    sys.path.insert(0, str(MODEL_DIR))
    import model  # noqa: E402: official dynamics implementation

    result_dir = OUT / name
    result_dir.mkdir(parents=True, exist_ok=True)
    model.run_exp(
        name,
        excited,
        result_dir,
        comp_path,
        conn_path,
        params=params,
        neu_slnc=silenced,
        n_proc=1,
        force_overwrite=True,
    )
    spikes = pd.read_parquet(result_dir / f"{name}.parquet")
    return {
        "condition": name,
        "spike_rows": int(len(spikes)),
        "active_neurons": int(spikes["flywire_id"].nunique()) if len(spikes) else 0,
        "dnp01_spikes": int(spikes["flywire_id"].isin(silenced).sum()) if len(spikes) else 0,
    }


def main() -> None:
    candidates = pd.read_csv(CANDIDATES)
    completeness = pd.read_csv(DATA_COMP, index_col=0)
    completeness.index = completeness.index.astype("int64")
    root_to_old = {int(root): i for i, root in enumerate(completeness.index)}
    lc4 = candidates.loc[candidates.cell_type.eq("LC4"), "root_id"].astype("int64").tolist()
    lplc2 = candidates.loc[candidates.cell_type.eq("LPLC2"), "root_id"].astype("int64").tolist()
    dnp01 = candidates.loc[candidates.cell_type.eq("DNp01"), "root_id"].astype("int64").tolist()
    seeds = [root for root in lc4[:3] + lplc2[:3] if root in root_to_old]
    targets = [root for root in dnp01 if root in root_to_old]
    if not seeds or not targets:
        raise SystemExit("Candidate root IDs do not overlap the official v783 model table.")

    seed_indices = {root_to_old[root] for root in seeds}
    target_indices = {root_to_old[root] for root in targets}
    nodes, edges = extract_subgraph(seed_indices, target_indices, hops=2)
    comp_path, conn_path, old_to_new = remap_and_write(nodes, edges, completeness)
    selected_roots = [int(completeness.index[old]) for old in sorted(nodes)]
    # Keep only roots present in the subgraph for the official model's ID lookup.
    selected_seeds = [root for root in seeds if root in selected_roots]
    selected_targets = [root for root in targets if root in selected_roots]

    sys.path.insert(0, str(MODEL_DIR))
    import model

    params = model.default_params.copy()
    params.update(t_run=100 * ms, n_run=1, r_poi=150 * Hz)
    baseline = run_official_condition("lc4_lplc2_activation", selected_seeds, [], params, comp_path, conn_path)
    silenced = run_official_condition("lc4_lplc2_activation_dnp01_silenced", selected_seeds, selected_targets, params, comp_path, conn_path)
    summary = {
        "dynamics_source": "external/official/drosophila-brain-model/model.py",
        "dataset": "FlyWire FAFB v783",
        "input_roots": selected_seeds,
        "dnp01_roots": selected_targets,
        "hops": 2,
        "subgraph_neurons": len(nodes),
        "subgraph_edges": len(edges),
        "conditions": [baseline, silenced],
        "interpretation": "Artificial LC4/LPLC2 activation in the official Brian2 LIF dynamics; subgraph reduction changes the graph scope but not the dynamics code.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

