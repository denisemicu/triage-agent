from __future__ import annotations

import os

from anthropic import Anthropic
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT, build_user_prompt
from schemas import TriageExtraction


load_dotenv()


def extract_application(
    application: dict,
    model: str | None = None
) -> TriageExtraction:
    """
    Use Claude to turn an application into a structured representation.
    """

    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    model = model or os.getenv(
        "CLAUDE_MODEL",
        "claude-sonnet-5"
    )

    response = client.messages.parse(
        model=model,
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(application),
            }
        ],
        output_format=TriageExtraction,
    )

    return response.parsed_output