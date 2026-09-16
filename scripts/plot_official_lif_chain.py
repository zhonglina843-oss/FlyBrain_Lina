#!/usr/bin/env python3
"""Plot the completed official LC4/LPLC2 -> DNp01 LIF chain experiment."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "official_lif_chain"
OUT = ROOT / "outputs" / "official_lif_chain_figure"

COLORS = {
    "LC4": "#2878B5",
    "LPLC2": "#D9892B",
    "DNp01": "#4D8C57",
    "edge": "#84909B",
    "text": "#202428",
}


def setup_style():
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
        }
    )


def short_id(value):
    return f"...{str(int(value))[-6:]}"


def draw_network(ax, selected, direct, dnp):
    selected = selected.copy()
    selected["y"] = np.r_[np.linspace(0.86, 0.56, 5), np.linspace(0.38, 0.08, 5)]
    selected["x"] = 0.12
    dn_y = {int(row.root_id): y for row, y in zip(dnp.itertuples(), [0.68, 0.28])}
    chosen = direct[direct.Presynaptic_ID.isin(selected.Presynaptic_ID)].copy()
    max_weight = max(float(chosen.Connectivity.max()), 1.0)

    for edge in chosen.itertuples():
        source = selected[selected.Presynaptic_ID.eq(edge.Presynaptic_ID)].iloc[0]
        target_y = dn_y[int(edge.Postsynaptic_ID)]
        width = 0.35 + 2.2 * float(edge.Connectivity) / max_weight
        arrow = FancyArrowPatch(
            (0.19, source.y),
            (0.77, target_y),
            connectionstyle="arc3,rad=0.05",
            arrowstyle="-|>",
            mutation_scale=7,
            linewidth=width,
            color=COLORS["edge"],
            alpha=0.55,
            zorder=1,
        )
        ax.add_patch(arrow)
        ax.text(0.47, (source.y + target_y) / 2 + 0.015, str(int(edge.Connectivity)),
                fontsize=5.3, color="#5B646C", ha="center", va="bottom")

    for row in selected.itertuples():
        color = COLORS[row.Presynaptic_Type]
        ax.scatter(row.x, row.y, s=72, color=color, edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(row.x - 0.025, row.y, short_id(row.Presynaptic_ID), ha="right", va="center",
                fontsize=5.7, color=COLORS["text"])

    for row in dnp.itertuples():
        y = dn_y[int(row.root_id)]
        ax.scatter(0.84, y, s=155, marker="s", color=COLORS["DNp01"],
                   edgecolor="white", linewidth=1, zorder=3)
        ax.text(0.90, y + 0.018, f"DNp01 {row.side}", ha="left", va="center",
                fontsize=7, weight="bold", color=COLORS["text"])
        ax.text(0.90, y - 0.035, short_id(row.root_id), ha="left", va="center",
                fontsize=5.7, color="#5B646C")

    ax.text(0.02, 0.95, "LC4", color=COLORS["LC4"], weight="bold", fontsize=7)
    ax.text(0.02, 0.47, "LPLC2", color=COLORS["LPLC2"], weight="bold", fontsize=7)
    ax.text(0.79, 0.95, "Descending readout", color=COLORS["DNp01"], weight="bold", fontsize=7)
    ax.text(0.47, 0.98, "direct connection count", ha="center", va="top",
            fontsize=5.8, color="#5B646C")
    ax.set_xlim(-0.08, 1.12)
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_spikes(ax, spikes, dnp):
    order = list(dnp.root_id.astype("int64"))
    labels = [f"DNp01 {side}" for side in dnp.side]
    for y, root_id in enumerate(order):
        t_ms = spikes.loc[spikes.flywire_id.eq(root_id), "t"].to_numpy() * 1000
        ax.hlines(y, 0, 100, color="#D5D9DC", linewidth=1.2, zorder=1)
        ax.vlines(t_ms, y - 0.22, y + 0.22, color=COLORS["DNp01"], linewidth=2, zorder=2)
        if t_ms.size:
            ax.text(t_ms.min() + 1.5, y + 0.28, f"first {t_ms.min():.1f} ms",
                    fontsize=5.8, color=COLORS["DNp01"], va="bottom")
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.55, len(labels) - 0.4)
    ax.set_xlabel("Simulation time (ms)")
    ax.set_ylabel("Official-model output")
    ax.grid(axis="x", color="#E6E8EA", linewidth=0.6)
    ax.tick_params(axis="both", length=2.5, width=0.7)
    ax.text(0.0, -0.43, "Poisson activation: 150 Hz; one 100 ms trial",
            transform=ax.transAxes, fontsize=5.8, color="#5B646C")


def main():
    setup_style()
    selected = pd.read_csv(DATA / "selected_inputs.csv")
    direct = pd.read_csv(DATA / "direct_lc4_lplc2_to_dnp01_edges.csv")
    dnp = pd.read_csv(DATA / "dnp01_summary.csv")
    spikes = pd.read_csv(DATA / "dnp01_spikes.csv")

    fig = plt.figure(figsize=(183 / 25.4, 92 / 25.4), constrained_layout=False)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1], wspace=0.26,
                          left=0.055, right=0.975, top=0.82, bottom=0.19)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    draw_network(ax_a, selected, direct, dnp)
    draw_spikes(ax_b, spikes, dnp)
    ax_a.text(-0.06, 1.04, "a", transform=ax_a.transAxes, fontsize=9, weight="bold")
    ax_b.text(-0.16, 1.04, "b", transform=ax_b.transAxes, fontsize=9, weight="bold")
    fig.suptitle("Official connectome-to-dynamics chain reaches bilateral DNp01",
                 x=0.055, y=0.965, ha="left", fontsize=10, weight="bold", color=COLORS["text"])
    fig.text(0.055, 0.90,
             "Five directly connected LC4 and five LPLC2 cells were artificially activated; "
             "edge counts come from FlyWire FAFB v783 and dynamics from the official Brian2 model.",
             ha="left", va="top", fontsize=6.5, color="#4F575E")
    fig.text(0.055, 0.035,
             "Interpretation boundary: optogenetic-style artificial input, one stochastic trial; "
             "not natural looming vision or escape behaviour.",
             ha="left", va="bottom", fontsize=6, color="#5B646C")

    OUT.mkdir(parents=True, exist_ok=True)
    base = OUT / "official_lif_chain"
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)
    print(base)


if __name__ == "__main__":
    main()
