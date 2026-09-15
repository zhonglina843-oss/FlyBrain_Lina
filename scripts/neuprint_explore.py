#!/usr/bin/env python3
"""Small, read-only neuPrint explorer for the FlyBrain pilot study."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding the shell environment."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List neuPrint datasets, search neuron types, or inspect partners."
    )
    parser.add_argument(
        "--server",
        default=None,
        help="neuPrint host (default: NEUPRINT_SERVER or neuprint.janelia.org)",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="dataset name (default: NEUPRINT_DATASET or hemibrain:v1.2.1)",
    )

    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("datasets", help="list datasets exposed by the server")

    search = commands.add_parser("search", help="search neuron types with a regex")
    search.add_argument("pattern", help="type regex, for example 'LC4.*'")
    search.add_argument("--limit", type=positive_int, default=20)
    search.add_argument("--csv", type=Path, help="optional CSV output path")

    partners = commands.add_parser("partners", help="show strong partners of one bodyId")
    partners.add_argument("body_id", type=positive_int)
    partners.add_argument(
        "--direction", choices=("upstream", "downstream"), default="downstream"
    )
    partners.add_argument("--min-weight", type=positive_int, default=5)
    partners.add_argument("--limit", type=positive_int, default=30)
    partners.add_argument("--csv", type=Path, help="optional CSV output path")
    return parser


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def create_client(args: argparse.Namespace):
    try:
        from neuprint import Client
    except ImportError as exc:
        raise SystemExit(
            "neuprint-python is missing. Run: python -m pip install -r requirements.txt"
        ) from exc

    server = args.server or os.getenv("NEUPRINT_SERVER", "neuprint.janelia.org")
    dataset = args.dataset or os.getenv("NEUPRINT_DATASET", "hemibrain:v1.2.1")
    token = os.getenv("NEUPRINT_APPLICATION_CREDENTIALS")
    if not token or token == "replace_with_your_personal_token":
        raise SystemExit(
            "Missing neuPrint token. Copy .env.example to .env and fill in "
            "NEUPRINT_APPLICATION_CREDENTIALS."
        )
    return Client(server, dataset=dataset, token=token)


def print_or_save(frame, csv_path: Path | None) -> None:
    if csv_path:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(csv_path, index=False)
        print(f"Saved {len(frame)} rows to {csv_path}")
    else:
        print(frame.to_string(index=False))


def run(args: argparse.Namespace) -> None:
    client = create_client(args)

    if args.command == "datasets":
        datasets = client.fetch_datasets(reload_cache=True)
        for name, metadata in sorted(datasets.items()):
            description = metadata.get("description", "") if metadata else ""
            print(f"{name}\t{description}")
        return

    from neuprint import NeuronCriteria as NC
    from neuprint import fetch_neurons, fetch_simple_connections

    if args.command == "search":
        neurons, _ = fetch_neurons(NC(type=args.pattern), client=client)
        columns = [
            col
            for col in ("bodyId", "type", "instance", "pre", "post", "status", "cropped")
            if col in neurons.columns
        ]
        result = neurons.loc[:, columns].head(args.limit)
        print_or_save(result, args.csv)
        return

    if args.direction == "downstream":
        frame = fetch_simple_connections(
            upstream_criteria=args.body_id,
            min_weight=args.min_weight,
            weight_props=["weight"],
            client=client,
        )
    else:
        frame = fetch_simple_connections(
            downstream_criteria=args.body_id,
            min_weight=args.min_weight,
            weight_props=["weight"],
            client=client,
        )

    result = frame.sort_values("weight", ascending=False).head(args.limit)
    print_or_save(result, args.csv)


def main() -> int:
    load_env_file(PROJECT_DIR / ".env")
    args = build_parser().parse_args()
    try:
        run(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"neuPrint query failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
