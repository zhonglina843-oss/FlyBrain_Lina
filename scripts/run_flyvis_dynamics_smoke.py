"""Run a compact FlyVis GPU dynamics check.

This intentionally uses the official FlyVis network with its bundled
connectome configuration. Pretrained weights are a separate optional step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from flyvis import Network


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--stimulus-start", type=int, default=5)
    parser.add_argument("--stimulus-stop", type=int, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(0)
    network = Network().to(device)
    stimulus = torch.zeros(1, args.frames, 1, 721, device=device)
    stimulus[:, args.stimulus_start : args.stimulus_stop] = 1.0
    activity = network.simulate(stimulus, 1 / 50)

    result = {
        "model": "TuragaLab/flyvis",
        "pretrained": False,
        "device": str(activity.device),
        "torch": torch.__version__,
        "cuda": bool(torch.cuda.is_available()),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "n_nodes": int(network.n_nodes),
        "n_edges": int(network.n_edges),
        "input_shape": list(stimulus.shape),
        "output_shape": list(activity.shape),
        "finite": bool(torch.isfinite(activity).all().item()),
        "baseline_mean": float(activity[:, : args.stimulus_start].mean().item()),
        "stimulus_mean": float(
            activity[:, args.stimulus_start : args.stimulus_stop].mean().item()
        ),
        "recovery_mean": float(activity[:, args.stimulus_stop :].mean().item()),
        "mean_frame_change": float((activity[:, 1:] - activity[:, :-1]).abs().mean().item()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
