#!/usr/bin/env python3
"""Publish precomputed no-science owner artifacts for workflow tests."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path


def _publish(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
        0o600,
    )
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("producer", "validator"))
    payload = parser.add_mutually_exclusive_group(required=True)
    payload.add_argument("--manifest", type=Path)
    payload.add_argument("--payload-base64")
    arguments = parser.parse_args()
    data = (
        arguments.manifest.read_bytes()
        if arguments.manifest is not None
        else base64.b64decode(arguments.payload_base64, validate=True)
    )
    record = json.loads(data)
    entries = (
        record["producer"] if arguments.mode == "producer" else [record["validation"]]
    )
    for entry in entries:
        _publish(Path(entry["path"]), base64.b64decode(entry["data_base64"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
