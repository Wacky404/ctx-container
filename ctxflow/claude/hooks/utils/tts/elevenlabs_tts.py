#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "pandas",
# ]
# ///

import os
import sys
import uuid
import datetime
import subprocess
from typing import Any
from pathlib import Path

from elevenlabs.client import ElevenLabs
from elevenlabs import play
import pandas as pd


HOME_DIR: str = os.path.expanduser("~")
_PERSISTENTAPISTORE = os.path.join(HOME_DIR, ".ctxflow", "api_calls.csv")
_AUDIOSTORE = os.path.join(HOME_DIR, ".ctxflow", "audio")
VOICE_ID = "56AoDkrOh6qfVPDXZ7Pt"
MODEL_ID = "eleven_turbo_v2_5"
OUTPUT_FORMAT = "mp3_44100_128"


def add_row(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """ add a row to a dataframe """
    df.loc[len(df)] = kwargs
    return df


def load_path(path: str) -> str:
    """
    handle path construction and makes sure the file is csv
    """
    if os.path.exists(path=path):
        try:
            name_ext: tuple[str, str] = os.path.splitext(
                os.path.basename(path))
            if name_ext[0] == 'api_calls' and name_ext[1] == '.csv':
                return path
        except Exception as e:
            return ""

    return ""


def main() -> None:
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment variables")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        elevenlabs = ElevenLabs(api_key=api_key)
        if len(sys.argv) > 1:
            text: str = " ".join(sys.argv[1:])
        else:
            text = "Time to be better than yesterday"

        path: str = load_path(_PERSISTENTAPISTORE)
        if path:
            df_apicalls: pd.DataFrame = pd.read_csv(path)
        else:
            os.makedirs(_PERSISTENTAPISTORE)
            df_apicalls = pd.DataFrame(
                columns=["text", "voice_id", "model_id", "output_format", "audio_path"])

        norm_text: str = text.lower().replace(" ", "")
        has_text = df_apicalls['text'].eq(norm_text).any()
        if has_text:
            matching_row = df_apicalls[df_apicalls['text'].eq(text)]
            path_to_audio: str = df_apicalls['audio_path'].iloc[0]
            subprocess.run(
                ["ffplay", "--nodisp", "--autoexit", f"{path_to_audio}"])
        else:
            try:

                audio = elevenlabs.text_to_speech.convert(
                    text=text,
                    voice_id=VOICE_ID,
                    model_id=MODEL_ID,
                    output_format=OUTPUT_FORMAT,
                )

                new_audio_path: str = os.path.join(
                    _AUDIOSTORE, f"cassidy_{str(uuid.uuid4())}.mp3")
                try:
                    with open(new_audio_path, 'wb') as fd:
                        fd.write(audio)
                    subprocess.run(
                        ["ffplay", "--nodisp", "--autoexit", new_audio_path])
                    df_apicalls = add_row(df=df_apicalls, **{
                        "text": norm_text,
                        "voice_id": VOICE_ID,
                        "model_id": MODEL_ID,
                        "output_format": OUTPUT_FORMAT,
                        "audio_path": new_audio_path,
                        "date_created": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                    })
                    df_apicalls.to_csv(path)
                except Exception as e:
                    pass

            except Exception:
                pass

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
