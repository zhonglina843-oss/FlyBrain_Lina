#!/usr/bin/env python3
"""Small reproducible smoke experiment for the official Shiu Brian2 model.

This is intentionally not a behavioral claim: LC4 activation is an artificial
optogenetic-style input, and DNp01 silencing is a causal network perturbation.
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
OUT = ROOT / "outputs" / "official_lif_smoke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration-ms", type=float, default=100.0)
    parser.add_argument("--input-rate-hz", type=float, default=150.0)
    parser.add_argument("--n-input", type=int, default=5)
    return parser.parse_args()


def run_condition(name, excited, silenced, params, model):
    result_dir = OUT / name
    result_dir.mkdir(parents=True, exist_ok=True)
    model.run_exp(
        name,
        excited,
        result_dir,
        MODEL_DIR / "Completeness_783.csv",
        MODEL_DIR / "Connectivity_783.parquet",
        params=params,
        neu_slnc=silenced,
        n_proc=1,
        force_overwrite=True,
    )
    path = result_dir / f"{name}.parquet"
    spikes = pd.read_parquet(path)
    return {
        "condition": name,
        "excited_root_ids": excited,
        "silenced_root_ids": silenced,
        "spike_rows": int(len(spikes)),
        "active_neurons": int(spikes["flywire_id"].nunique()) if len(spikes) else 0,
        "trials": int(spikes["trial"].nunique()) if len(spikes) else 0,
    }


def main() -> None:
    args = parse_args()
    if not CANDIDATES.exists():
        raise SystemExit(f"Missing candidate table: {CANDIDATES}")

    sys.path.insert(0, str(MODEL_DIR))
    import model  # official repository module

    candidates = pd.read_csv(CANDIDATES)
    lc4 = candidates.loc[candidates.cell_type.eq("LC4"), "root_id"].astype("int64").tolist()
    dnp01 = candidates.loc[candidates.cell_type.eq("DNp01"), "root_id"].astype("int64").tolist()
    if len(lc4) < args.n_input or not dnp01:
        raise SystemExit("Candidate table does not contain enough LC4/DNp01 IDs.")

    params = model.default_params.copy()
    params.update(
        t_run=args.duration_ms * ms,
        n_run=1,
        r_poi=args.input_rate_hz * Hz,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = run_condition("lc4_activation", lc4[: args.n_input], [], params, model)
    silenced = run_condition("lc4_activation_dnp01_silenced", lc4[: args.n_input], dnp01, params, model)
    summary = {
        "model": "philshiu/Drosophila_brain_model",
        "dataset": "FlyWire FAFB v783",
        "duration_ms": args.duration_ms,
        "input_rate_hz": args.input_rate_hz,
        "n_input_lc4": args.n_input,
        "conditions": [baseline, silenced],
        "interpretation": "Artificial LC4 activation followed by whole-network spike propagation; DNp01 silencing is a causal perturbation, not a behavioral simulation.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
