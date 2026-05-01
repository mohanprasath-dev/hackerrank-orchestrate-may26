from __future__ import annotations

import os
import traceback
from typing import Dict, List

from google import genai
from google.genai import types


def generate_response(
    issue: str,
    subject: str,
    company: str,
    status: str,
    request_type: str,
    product_area: str,
    retrieved_chunks: List[Dict],
) -> str:
    """Generate a user-facing response with the Gemini SDK and return raw text."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set")

        top_chunks = retrieved_chunks[:3]
        excerpts = "\n---\n".join(chunk.get("text", "") for chunk in top_chunks)

        prompt = (
            "You are a support triage agent. Answer ONLY using the provided support corpus excerpts. "
            "Do not hallucinate policies. Do not invent steps. If the status is \"escalated\", your response must be a polite message "
            "telling the user their issue has been escalated to a human agent and why. If \"replied\", answer directly from the corpus.\n\n"
            f"Company: {company}\n"
            f"Issue: {issue}\n"
            f"Status decided: {status}\n"
            f"Request type: {request_type}\n"
            f"Product area: {product_area}\n\n"
            "Relevant corpus excerpts:\n"
            f"{excerpts}\n\n"
            "Respond in this exact XML format:\n"
            "<response>user-facing reply here</response>\n"
            "<justification>one sentence explaining routing decision and corpus basis</justification>"
        )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=8192,
            ),
        )

        raw_text = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    raw_text += part.text
        print("RAW:", raw_text[:200])
        return raw_text
    except Exception as exc:
        print("generate_response failed with exception:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        raise


