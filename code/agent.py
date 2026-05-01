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

        # Get top retrieved chunks
        top_chunks = retrieved_chunks[:3]
        excerpts = "\n---\n".join(chunk.get("text", "") for chunk in top_chunks)

        # Extract top score if available
        top_score = None
        if top_chunks and isinstance(top_chunks[0], dict) and "score" in top_chunks[0]:
            try:
                top_score = float(top_chunks[0]["score"])
            except Exception:
                top_score = None

        # Optional score text blocks
        score_text = (
            f"Retrieval confidence for top excerpt: {top_score:.2f}\n\n"
            if top_score is not None
            else ""
        )

        justification_text = (
            f"<justification>one sentence explaining routing decision and corpus basis. Retrieved with confidence: {top_score:.2f}</justification>"
            if top_score is not None
            else "<justification>one sentence explaining routing decision and corpus basis</justification>"
        )

        # Build prompt (safe multi-line format)
        prompt = f"""
You are a support triage agent. Answer ONLY using the provided support corpus excerpts.
Do not hallucinate policies. Do not invent steps.

If the status is "escalated", respond with a polite message telling the user their issue has been escalated to a human agent and why.
If the status is "replied", answer directly from the corpus.

Company: {company}
Issue: {issue}
Status decided: {status}
Request type: {request_type}
Product area: {product_area}

Relevant corpus excerpts:
{excerpts}

{score_text}Respond in this exact XML format:
<response>user-facing reply here</response>
{justification_text}
"""

        # Initialize Gemini client
        client = genai.Client(api_key=api_key)

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=8192,
            ),
        )

        # Extract text safely
        raw_text = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    raw_text += part.text

        print("RAW:", raw_text[:200])
        return raw_text

    except Exception as exc:
        print("generate_response failed with exception:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        raise