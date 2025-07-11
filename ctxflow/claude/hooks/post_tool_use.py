#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    try:
        input_data: dict[Any, ...] = json.load(sys.stdin)

        log_dir: Path = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path: Path = log_dir / 'post_tool_use.json'

        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data: list[Any] = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        log_data.append(input_data)

        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == '__main__':
    main()
