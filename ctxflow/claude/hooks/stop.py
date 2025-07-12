#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///

import argparse
import json
import os
import sys
import random
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List


SUCCEED = 0
FAIL = 1
BLOCK = 2


def get_completion_messages() -> List[str]:
    """ Return list of friendly completion messages. """
    return [
        "The agents work is complete",
        "Claude is done!",
        "Task finished!",
        "Job complete!",
        "Your agent is ready for the next task",
        "Agentic work completed",
        "Work complete, might be a new record time",
        "You might want to check your account balance, task is done",
        "Your checkings definitely overdrafted on this one",
        "Job is done, good luck debugging that"
    ]


def get_tts_script_path() -> Optional[str]:
    """
    Determine which TTS script to use based on available API keys.
    For now its just elevenlabs
    """
    script_dir: Path = Path(__file__).parent
    tts_dir: Path = script_dir / "utils" / "tts"

    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)

    return None


def get_llm_completion_message() -> str:
    """
    Generate completion message using available LLM services.
    Will only make api call like 15% of the time
    """
    script_dir: Path = Path(__file__).parent
    llm_dir: Path = script_dir / "utils" / "llm"

    if random.random() <= 0.15:

        if os.getenv('ANTHROPIC_API_KEY'):
            anth_script: Path = llm_dir / "anth.py"
            if anth_script.exists():
                try:
                    result: subprocess.CompletedProcess[Any] = subprocess.run([
                        "uv", "run", str(anth_script), "--completion"
                    ],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
        elif os.getenv('OPENAI_API_KEY'):
            oai_script: Path = llm_dir / "oai.py"
            if oai_script.exists():
                try:
                    result = subprocess.run([
                        "uv", "run", str(oai_script), "--completion"
                    ],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        return result.stdout.strip()
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass

    # Fallback to random predefined message
    messages: list[str] = get_completion_messages()
    return random.choice(messages)


def announce_completion() -> None:
    """ Announce completion using the best available TTS service. """
    try:
        tts_script: str | None = get_tts_script_path()
        if not tts_script:
            return

        completion_message: str = get_llm_completion_message()

        subprocess.run([
            "uv", "run", tts_script, completion_message
        ],
            capture_output=True,
            timeout=10,
            check=True,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, subprocess.CalledProcessError, FileNotFoundError):
        pass
    except Exception:
        pass


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--chat', action='store_true',
                            help='Copy transcript to chat.json')
        args: argparse.Namespace = parser.parse_args()

        input_data: dict[Any, ...] = json.load(sys.stdin)

        session_id: str = input_data.get("session_id", "")
        stop_hook_active: bool = input_data.get("stop_hook_active", False)

        log_dir: str = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path: str = os.path.join(log_dir, "stop.json")

        # read existing log data or initialize empty list
        if os.path.exists(log_path):
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

        # handle --chat switch
        if args.chat and 'transcript_path' in input_data:
            transcript_path: str = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # read .jsonl file and convert to JSON array
                chat_data = []
                try:
                    with open(transcript_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    chat_data.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass

                    # write to logs/chat.json
                    chat_file: str = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass

        announce_completion()
        sys.exit(SUCCEED)

    except json.JSONDecodeError:
        sys.exit(FAIL)
    except Exception:
        sys.exit(FAIL)


if __name__ == "__main__":
    main()
