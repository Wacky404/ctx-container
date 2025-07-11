#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


def get_tts_script_path() -> Optional[str]:
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    script_dir: Path = Path(__file__).parent
    tts_dir: Path = script_dir / "utils" / "tts"

    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)

    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)

    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)

    return None


def announce_subagent_completion() -> None:
    """ Announce subagent completion using the best available TTS service. """
    try:
        tts_script: str | None = get_tts_script_path()
        if not tts_script:
            return

        completion_message = "Subagent Task Complete"
        subprocess.run([
            "uv", "run", tts_script, completion_message
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
        parser.add_argument('--chat', action='store_true',
                            help='Copy transcript to chat.json')
        args: argparse.Namespace = parser.parse_args()

        input_data: dict[Any, ...] = json.load(sys.stdin)

        session_id: str = input_data.get("session_id", "")
        stop_hook_active: bool = input_data.get("stop_hook_active", False)

        log_dir: str = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_path: str = os.path.join(log_dir, "subagent_stop.json")
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

        # Handle --chat switch (same as stop.py)
        if args.chat and 'transcript_path' in input_data:
            transcript_path = input_data['transcript_path']
            if os.path.exists(transcript_path):
                # Read .jsonl file and convert to JSON array
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

                    # Write to logs/chat.json
                    chat_file = os.path.join(log_dir, 'chat.json')
                    with open(chat_file, 'w') as f:
                        json.dump(chat_data, f, indent=2)
                except Exception:
                    pass

        announce_subagent_completion()
        sys.exit(0)

    except json.JSONDecodeError:
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
