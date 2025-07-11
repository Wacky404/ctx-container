#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai"
# ]
# ///

import os
import sys
from typing import Any, Optional


def prompt_llm(prompt_text: str) -> Optional[str]:
    """ Base OpenAI LLM. """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception:
        return None


def generate_completion_message() -> Optional[str]:
    """ Generate a completion message using OpenAI LLM. """
    engineer_name: str = os.getenv("ENGINEER_NAME", "").strip()
    if engineer_name:
        name_instruction: str = f"Sometimes (about 30% of the time) include the engineer's name '{engineer_name}' in a natural way."
        examples: str = f"""Examples of the style:
- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"
- Personalized: "{engineer_name}, all set!", "Ready for you, {engineer_name}!", "Complete, {engineer_name}!", "{engineer_name}, we're done!" """
    else:
        name_instruction = ""
        examples = """Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!" """

    prompt: str = f"""Generate a short, friendly completion message for when an AI coding assistant finishes a task.

Requirements:
- Keep it under 10 words
- Make it positive and future focused
- Use natural, conversational language
- Focus on completion/readiness
- Do NOT include quotes, formatting, or explanations
- Return ONLY the completion message text
{name_instruction}

{examples}

Generate ONE completion message:"""

    response: str | None = prompt_llm(prompt)
    if response:
        response = response.strip().strip('"').strip("'").strip()
        # take first line if multiple lines
        response = response.split("\n")[0].strip()

    return response


def main() -> None:
    if len(sys.argv) > 1:
        if sys.argv[1] == "--completion":
            message = generate_completion_message()
            if message:
                print(message)
            else:
                print("Error generating completion message")
        else:
            prompt_text = " ".join(sys.argv[1:])
            response = prompt_llm(prompt_text)
            if response:
                print(response)
            else:
                print("Error calling OpenAI API")
    else:
        print("Usage: ./oai.py 'your prompt here' or ./oai.py --completion")


if __name__ == "__main__":
    main()
