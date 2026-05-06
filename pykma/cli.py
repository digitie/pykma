"""Command line entrypoint for pykma."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any
from typing import Sequence

from .apihub import ApiHubClient
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

    apihub_parser = subparsers.add_parser("apihub")
    apihub_parser.add_argument("path", help="APIHub /api/... path")
    apihub_parser.add_argument("--auth-key", help="APIHub authKey. Defaults to KMA_APIHUB_AUTH_KEY.")
    apihub_parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Query parameter in key=value form. Can be repeated.",
    )

    args = parser.parse_args(argv)
    if args.command == "apihub":
        params = _parse_params(args.param)
        client = (
            ApiHubClient(auth_key=args.auth_key)
            if args.auth_key
            else ApiHubClient.from_env()
        )
        response = client.request_path(args.path, params)
        print(response.text)
        return 0

    location = _location_kwargs(args)
    client = (
        KmaClient(service_key=args.service_key)
        if args.service_key
        else KmaClient.from_env()
    )

    if args.command == "now":
        print(json.dumps(_jsonable(client.now(**location)), ensure_ascii=False, default=str, indent=2))
        return 0

    forecast = client.forecast_short(**location) if args.short else client.forecast(**location)
    print(json.dumps(_jsonable(forecast), ensure_ascii=False, default=str, indent=2))
    return 0


def _jsonable(value: Any) -> Any:
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return asdict(value)
    return value


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


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--param must be key=value, got {value!r}")
        key, raw = value.split("=", 1)
        if not key:
            raise SystemExit("--param key must not be empty")
        params[key] = raw
    return params


if __name__ == "__main__":
    raise SystemExit(main())
