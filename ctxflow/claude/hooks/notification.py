#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///

import argparse
import json
import os
import sys
import subprocess
import random
from typing import Optional, Any
from pathlib import Path


SUCCEED = 0
FAIL = 1
BLOCK = 2


def get_tts_script_path() -> Optional[str]:
    """
    Determine which TTS script to use based on available API keys.
    Just elevenlabs for now
    """
    script_dir: Path = Path(__file__).parent
    tts_dir: Path = script_dir / "utils" / "tts"

    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script: Path = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)

    return None


def announce_notification() -> None:
    """ Announce that the agent needs user input. """
    try:
        tts_script: str | None = get_tts_script_path()
        if not tts_script:
            return

        engineer_name: str = os.getenv('ENGINEER_NAME', '').strip()
        if engineer_name and random.random() < 0.40:
            notification_message: str = f"{engineer_name}, your agent needs your input"
        else:
            notification_message = "Your agent needs your input"

        subprocess.run([
            "uv", "run", tts_script, notification_message
        ],
            capture_output=True,
            timeout=10
        )

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    except Exception:
        pass


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--notify', action='store_true',
                            help='Enable TTS notifications')
        args: argparse.Namespace = parser.parse_args()

        input_data: dict[Any, ...] = json.load(sys.stdin)

        log_dir: str = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file: str = os.path.join(log_dir, 'notification.json')
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                try:
                    log_data: list[Any] = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        log_data.append(input_data)

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

        # announce notification via TTS only if --notify flag is set
        if args.notify:
            announce_notification()

        sys.exit(SUCCEED)

    except json.JSONDecodeError:
        sys.exit(FAIL)
    except Exception:
        sys.exit(FAIL)


if __name__ == '__main__':
    main()
