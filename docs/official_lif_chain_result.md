# Official LIF Chain Result

Run date: 2026-09-16.

## Question

When directly connected LC4 and LPLC2 cells are artificially activated, does the official Shiu et al. Brian2 model propagate spikes to the two DNp01 cells?

## Provenance

- Connectivity: `Completeness_783.csv` and `Connectivity_783.parquet` bundled in `philshiu/Drosophila_brain_model`.
- Dynamics: unchanged `model.py` from that repository.
- Custom experiment code: `scripts/run_official_lif_chain.py`.
- Custom operations: select inputs, extract a one-hop induced graph, invoke `model.run_exp`, and summarize spikes.

## Input

- Five LC4 and five LPLC2 cells.
- Cells were selected deterministically as the five strongest direct partners of DNp01 per type by official `Connectivity` count.
- Each selected cell received the official model's Poisson activation at 150 Hz.
- One trial lasting 100 ms.

## Local graph

| Metric | Value |
|---|---:|
| Neurons | 1,062 |
| Connections | 50,385 |
| Candidate LC4/LPLC2 -> DNp01 direct edges | 293 |
| Active neurons | 39 |
| Recorded spike rows | 217 |

## DNp01 response

| Side | Root ID | Spikes | First spike |
|---|---:|---:|---:|
| Right | 720575940632499757 | 4 | 10.5 ms |
| Left | 720575940622838154 | 2 | 32.3 ms |

## Interpretation boundary

This completes the technical chain `official connectivity -> artificial LC4/LPLC2 activation -> official LIF dynamics -> DNp01 spikes`. It does not demonstrate natural looming vision, escape behavior, motor planning, or an embodied fly. Those require a visual encoder, VNC/body model, action readout, and behavioral validation.

