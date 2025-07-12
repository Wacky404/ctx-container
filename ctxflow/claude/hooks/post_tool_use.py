#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import sys
from pathlib import Path
from typing import Any


SUCCEED = 0
FAIL = 1
BLOCK = 2


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

        sys.exit(SUCCEED)

    except json.JSONDecodeError:
        sys.exit(FAIL)
    except Exception:
        sys.exit(FAIL)


if __name__ == '__main__':
    main()
