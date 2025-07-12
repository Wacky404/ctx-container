#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
from pathlib import Path
from typing import Any


SUCCEED = 0
FAIL = 1
BLOCK = 2


def is_dangerous_rm_command(command: str) -> bool:
    """
    Comprehensive detection of dangerous rm commands.
    Matches various forms of rm -rf and similar destructive patterns.
    """
    normalized: str = ' '.join(command.lower().split())

    patterns: list[str] = [
        r'\brm\s+.*-[a-z]*r[a-z]*f',  # rm -rf, rm -fr, rm -Rf, etc.
        r'\brm\s+.*-[a-z]*f[a-z]*r',  # rm -fr variations
        r'\brm\s+--recursive\s+--force',  # rm --recursive --force
        r'\brm\s+--force\s+--recursive',  # rm --force --recursive
        r'\brm\s+.*-[a-z]*r',  # rm -r (recursive without force)
        r'\brm\s+-r\s+.*-f',  # rm -r ... -f
        r'\brm\s+-f\s+.*-r',  # rm -f ... -r
    ]

    for pattern in patterns:
        if re.search(pattern, normalized):
            return True

    dangerous_paths: list[str] = [
        r'/',           # Root directory
        r'/\*',         # Root with wildcard
        r'~',           # Home directory
        r'~/',          # Home directory path
        r'\$HOME',      # Home environment variable
        r'\.\.',        # Parent directory references
        r'\*',          # Wildcards in general rm -rf context
        r'\.',          # Current directory
        r'\.\s*$',      # Current directory at end of command
    ]

    if re.search(r'\brm\s+.*-[a-z]*r', normalized):
        for path in dangerous_paths:
            if re.search(path, normalized):
                return True

    return False


def is_env_file_access(tool_name: str, tool_input: dict[Any, ...]) -> bool:
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write', 'Bash']:
        if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
            file_path: str = tool_input.get('file_path', '')
            if '.env' in file_path and not file_path.endswith('.env.sample'):
                return True
        elif tool_name == 'Bash':
            command: str = tool_input.get('command', '')
            env_patterns: list[str] = [
                r'\b\.env\b(?!\.sample)',  # .env but not .env.sample
                r'cat\s+.*\.env\b(?!\.sample)',  # cat .env
                r'echo\s+.*>\s*\.env\b(?!\.sample)',  # echo > .env
                r'touch\s+.*\.env\b(?!\.sample)',  # touch .env
                r'cp\s+.*\.env\b(?!\.sample)',  # cp .env
                r'mv\s+.*\.env\b(?!\.sample)',  # mv .env
            ]

            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True

    return False


def main() -> None:
    try:
        input_data: dict[Any, ...] = json.load(sys.stdin)

        tool_name: str = input_data.get('tool_name', '')
        tool_input: dict[Any, ...] = input_data.get('tool_input', {})

        if is_env_file_access(tool_name, tool_input):
            print(
                "BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(BLOCK)

        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            if is_dangerous_rm_command(command):
                print(
                    "BLOCKED: Dangerous rm command detected and prevented", file=sys.stderr)
                sys.exit(BLOCK)

        log_dir: Path = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path: Path = log_dir / 'pre_tool_use.json'
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
