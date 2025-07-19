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

SUCCEED = 0
FAIL = 1

HOME_DIR: str = os.path.expanduser("~")
_PERSISTENTAPISTORE = os.path.join(HOME_DIR, ".ctxflow", "api_calls.csv")
_AUDIOSTORE = os.path.join(HOME_DIR, ".ctxflow", "audio")
VOICE_ID = "56AoDkrOh6qfVPDXZ7Pt"
MODEL_ID = "eleven_turbo_v2_5"
OUTPUT_FORMAT = "mp3_44100_128"


def add_row(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    df.loc[len(df)] = kwargs
    return df


def main() -> None:
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment variables")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        sys.exit(FAIL)

    try:
        elevenlabs = ElevenLabs(api_key=api_key)
        if len(sys.argv) > 1:
            text: str = " ".join(sys.argv[1:])
        else:
            text = "Time to be better than yesterday"

        try:
            df_apicalls: pd.DataFrame = pd.read_csv(_PERSISTENTAPISTORE)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_apicalls = pd.DataFrame(
                columns=["text", "voice_id", "model_id", "output_format", "audio_path", "date_created"])
            df_apicalls.to_csv(_PERSISTENTAPISTORE, index=False)

        norm_text: str = text.lower().replace(" ", "")
        matching_row = df_apicalls[df_apicalls['text'].eq(norm_text)]
        if not matching_row.empty:
            path_to_audio: str = matching_row['audio_path'].iloc[0]
            print(f"Playing cached audio: {path_to_audio}")
            try:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", f"{path_to_audio}"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error playing audio: {e}")
            except FileNotFoundError:
                print(
                    "ffplay not found. Install ffmpeg or use a different audio player.")
        else:
            print(f"Generating new audio for: '{text}'")
            try:
                # testing, voice was fast at 1.0
                # 7 was a little tism; too slow
                audio = elevenlabs.text_to_speech.convert(
                    text=text,
                    voice_id=VOICE_ID,
                    model_id=MODEL_ID,
                    output_format=OUTPUT_FORMAT,
                    voice_settings={
                        "stability": 0.8,
                        "style": 0,
                        "speed": 0.9,
                    }
                )

                new_audio_path: str = os.path.join(
                    _AUDIOSTORE, f"cassidy_{str(uuid.uuid4())}.mp3")

                print(f"Saving audio to: {new_audio_path}")

                with open(new_audio_path, 'wb') as fd:
                    for chunk in audio:
                        if isinstance(chunk, bytes):
                            fd.write(chunk)

                print("Audio saved successfully")

                df_apicalls = add_row(df=df_apicalls, **{
                    "text": norm_text,
                    "voice_id": VOICE_ID,
                    "model_id": MODEL_ID,
                    "output_format": OUTPUT_FORMAT,
                    "audio_path": new_audio_path,
                    "date_created": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
                })

                df_apicalls.to_csv(_PERSISTENTAPISTORE, index=False)
                print("CSV updated successfully")

                try:
                    print("Playing audio...")
                    subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", new_audio_path], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error playing audio: {e}")
                except FileNotFoundError:
                    print(
                        "ffplay not found. Install ffmpeg or use a different audio player.")

            except Exception as e:
                print(f"Error generating or saving audio: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(FAIL)


if __name__ == "__main__":
    main()
