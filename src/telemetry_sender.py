import argparse
import asyncio
import configparser
import uuid
from pathlib import Path

from src.telemetry.gps_reader import GpsSerialSource
from src.telemetry.link_quality import read_link_quality_pct
from src.telemetry.message_builder import build_message
from src.telemetry.ndjson_logger import NdjsonLogger
from src.telemetry.replay_source import ReplaySource
from src.telemetry.server import TelemetryServer
from src.telemetry.simulated_source import SimulatedSource

_DEFAULTS = {
    "source": "simulate",
    "serial_port": "/dev/ttyACM0",
    "baud_rate": "9600",
    "ws_host": "0.0.0.0",
    "ws_port": "8765",
    "wifi_interface": "wlan0",
    "data_dir": "data",
}


def _load_config_defaults(config_path) -> dict:
    defaults = dict(_DEFAULTS)
    if config_path:
        parser = configparser.ConfigParser()
        parser.read(config_path)
        if parser.has_section("sender"):
            defaults.update(parser["sender"])
    return defaults


def _parse_args():
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", help="path to a sender.ini-style config file")
    pre_args, remaining_argv = pre_parser.parse_known_args()
    defaults = _load_config_defaults(pre_args.config)

    parser = argparse.ArgumentParser(
        description="Boat-side GPS telemetry sender", parents=[pre_parser]
    )
    parser.add_argument("--source", choices=["gps", "simulate", "replay"], default=defaults["source"])
    parser.add_argument("--serial-port", default=defaults["serial_port"])
    parser.add_argument("--baud-rate", type=int, default=int(defaults["baud_rate"]))
    parser.add_argument("--replay-file")
    parser.add_argument("--replay-fast", action="store_true")
    parser.add_argument("--ws-host", default=defaults["ws_host"])
    parser.add_argument("--ws-port", type=int, default=int(defaults["ws_port"]))
    parser.add_argument("--wifi-interface", default=defaults["wifi_interface"])
    parser.add_argument("--data-dir", default=defaults["data_dir"])
    return parser.parse_args(remaining_argv)


def _build_source(args):
    if args.source == "gps":
        return GpsSerialSource(args.serial_port, args.baud_rate)
    if args.source == "simulate":
        return SimulatedSource()
    if args.source == "replay":
        if not args.replay_file:
            raise SystemExit("--replay-file is required when --source replay")
        return ReplaySource(Path(args.replay_file), realtime=not args.replay_fast)
    raise ValueError(f"unknown source: {args.source}")


async def _run(args) -> None:
    source = _build_source(args)
    server = TelemetryServer(args.ws_host, args.ws_port)
    server_task = asyncio.create_task(server.run_forever())

    # Generated once per process start and sent unchanged on every message,
    # so the shore app can tell a boat reboot (a new session_id) apart from
    # its sequence counter simply resuming mid-run.
    session_id = uuid.uuid4().hex

    sequence = 0
    with NdjsonLogger(Path(args.data_dir)) as logger:
        async for fix in source:
            sequence += 1
            link_quality_pct = read_link_quality_pct(args.wifi_interface)
            message = build_message(
                fix, sequence, link_quality_pct, session_id=session_id, source=args.source
            )
            logger.write(message)
            server.broadcast(message)

    server_task.cancel()


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
