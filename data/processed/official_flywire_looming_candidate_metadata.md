---
dataset: FlyWire FAFB v783 (female adult brain)
annotation_source: flyconnectome/flywire_annotations v3.1.0
generated_on: 2026-09-15
scope: static annotation audit; not a connectivity query
---

# Official Candidate Metadata

This record was generated from the pinned official annotation dump. It establishes that the named cell types and representative root IDs exist in the annotation release. It does not establish direct LC4/LPLC2 -> DNp01 edges; that requires an explicit Codex/CAVE connectivity query.

## Counts

| Cell type | Annotated neurons |
|---|---:|
| LC4 | 104 |
| LPLC2 | 210 |
| DNp01 | 2 |

## Representative cells

| Type | root ID | superclass | side | predicted transmitter | known transmitter | annotation source |
|---|---:|---|---|---|---|---|
| LC4 | 720575940618002644 | visual_projection | left | acetylcholine (0.5835598448005004) | acetylcholine | Davis et al., 2020 (TAPIN) |
| LPLC2 | 720575940626745392 | visual_projection | right | acetylcholine (0.5938895305175015) | acetylcholine | Davis et al., 2020 (TAPIN) |
| DNp01 | 720575940632499757 | descending | right | glutamate (0.26569821946215116) | not listed | not listed |

## Next manual query

Use Codex with dataset `FAFB v783 (CB)` to query direct partners for the representative IDs and save the returned edge weight, ROI and query URL. Do not infer physiological strength from synapse count alone.
