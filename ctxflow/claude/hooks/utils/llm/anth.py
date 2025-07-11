#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "anthropic"
# ]
# ///

import os
import sys
from typing import Any, Optional


def prompt_llm(prompt_text: str) -> Optional[str]:
    """ Base Anthropic LLM. """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt_text}],
        )
        return message.content[0].text.strip()

    except Exception:
        return None


def generate_completion_message() -> Optional[str]:
    """ Generate a completion message using Anthropic LLM. """
    engineer_name = os.getenv("ENGINEER_NAME", "").strip()
    if engineer_name:
        name_instruction: str = f"Sometimes (about 30% of the time) include the engineer's name '{engineer_name}' in a natural way."
        examples: str = f"""Examples of the style:
- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"
- Personalized: "{engineer_name}, all set!", "Ready for you, {engineer_name}!", "Complete, {engineer_name}!", "{engineer_name}, we're done!" """
    else:
        name_instruction = ""
        examples = """Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!" """

    prompt = f"""Generate a short, friendly completion message for when an AI coding assistant finishes a task.

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

    response = prompt_llm(prompt)
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
                print("Error calling Anthropic API")
    else:
        print("Usage: ./anth.py 'your prompt here' or ./anth.py --completion")


if __name__ == "__main__":
    main()
