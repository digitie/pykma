"""Command line entrypoint for pykma."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from .client import KmaClient


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pykma")
    parser.add_argument("--service-key", help="KMA decoded service key. Defaults to KMA_SERVICE_KEY.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    now_parser = subparsers.add_parser("now")
    _add_location_args(now_parser)

    forecast_parser = subparsers.add_parser("forecast")
    _add_location_args(forecast_parser)
    forecast_parser.add_argument("--short", action="store_true", help="Use ultra-short forecast.")

    args = parser.parse_args(argv)
    location = _location_kwargs(args)
    client = (
        KmaClient(service_key=args.service_key)
        if args.service_key
        else KmaClient.from_env()
    )

    if args.command == "now":
        print(json.dumps(asdict(client.now(**location)), ensure_ascii=False, default=str, indent=2))
        return 0

    forecast = client.forecast_short(**location) if args.short else client.forecast(**location)
    print(json.dumps([asdict(item) for item in forecast], ensure_ascii=False, default=str, indent=2))
    return 0


def _add_location_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lat", type=float)
    group.add_argument("--nx", type=int)
    parser.add_argument("--lon", type=float)
    parser.add_argument("--ny", type=int)


def _location_kwargs(args: argparse.Namespace) -> dict[str, float | int]:
    if args.lat is not None:
        if args.lon is None:
            raise SystemExit("--lon is required with --lat")
        return {"lat": args.lat, "lon": args.lon}
    if args.ny is None:
        raise SystemExit("--ny is required with --nx")
    return {"nx": args.nx, "ny": args.ny}


if __name__ == "__main__":
    raise SystemExit(main())
