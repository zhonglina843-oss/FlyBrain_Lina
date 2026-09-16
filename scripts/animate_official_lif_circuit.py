"""Create a compact 3-D animation of the measured LC4/LPLC2 -> DNp01 circuit.

Input nodes are shown as stimulated throughout the 100 ms trial. DNp01 nodes
flash at the recorded spike times. The animation is intentionally a circuit
view, not a claim that all upstream spike times were recorded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--spikes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inputs = pd.read_csv(args.input)
    spikes = pd.read_csv(args.spikes)
    inputs = inputs.drop_duplicates("Presynaptic_ID").reset_index(drop=True)
    outputs = sorted(spikes["flywire_id"].unique())

    rng = np.random.default_rng(4)
    input_pos = np.column_stack(
        [
            np.linspace(-1.2, 1.2, len(inputs)),
            np.where(inputs["Presynaptic_Type"].eq("LC4"), 0.35, -0.35),
            np.zeros(len(inputs)),
        ]
    )
    output_pos = {
        int(root): np.array([(-0.28 if i == 0 else 0.28), 0.0, 1.65])
        for i, root in enumerate(outputs)
    }
    # Use direct measured edges to define the displayed circuit.
    direct = pd.read_csv(args.input.parent / "direct_lc4_lplc2_to_dnp01_edges.csv")
    edge_targets = {
        int(row.Presynaptic_ID): output_pos[int(row.Postsynaptic_ID)]
        for _, row in direct.iterrows()
        if int(row.Postsynaptic_ID) in output_pos
    }

    frames = np.linspace(0, 0.1, 31)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(7.2, 5.6), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    input_colors = ["#2A6FBB" if x == "LC4" else "#D97732" for x in inputs["Presynaptic_Type"]]

    def render(frame_idx: int):
        t = frames[frame_idx]
        ax.clear()
        ax.set_xlim(-1.55, 1.55); ax.set_ylim(-0.8, 0.8); ax.set_zlim(-0.25, 2.15)
        ax.view_init(elev=20, azim=-62); ax.set_axis_off()
        for _, row in inputs.iterrows():
            dst = edge_targets.get(int(row.Presynaptic_ID))
            if dst is not None:
                src = input_pos[int(row.name)]
                ax.plot([src[0], dst[0]], [src[1], dst[1]], [src[2], dst[2]], color="#B8C2CC", linewidth=0.7, alpha=0.45)
        ax.scatter(input_pos[:, 0], input_pos[:, 1], input_pos[:, 2], s=75, c=input_colors, edgecolors="white", linewidths=0.6, depthshade=False)
        for i, row in inputs.iterrows():
            ax.text(input_pos[i, 0], input_pos[i, 1], -0.12, row.Presynaptic_Type, fontsize=7, ha="center", color="#24313D")
        for root, pos in output_pos.items():
            count = int(((spikes["flywire_id"] == root) & (spikes["t"] <= t)).sum())
            active = ((spikes["flywire_id"] == root) & (np.abs(spikes["t"] - t) < 0.0025)).any()
            ax.scatter([pos[0]], [pos[1]], [pos[2]], s=220 if active else 120, c="#C43D3D" if active else "#7D1F2A", edgecolors="white", linewidths=0.8, depthshade=False)
            side = "right" if root == max(output_pos) else "left"
            ax.text(pos[0], pos[1], pos[2] + 0.13, f"DNp01 {side}\n{count} spikes", fontsize=7, ha="center")
        ax.text2D(0.03, 0.95, f"Official LIF local circuit   t = {t * 1000:05.1f} ms", transform=ax.transAxes, fontsize=10, weight="bold", color="#18232E")
        ax.text2D(0.03, 0.04, "Blue/orange: stimulated LC4/LPLC2   red: recorded DNp01 spike", transform=ax.transAxes, fontsize=7.5, color="#53616E")
        return ax,

    animation = FuncAnimation(fig, render, frames=len(frames), interval=100, blit=False)
    animation.save(args.output, writer=PillowWriter(fps=10))
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
