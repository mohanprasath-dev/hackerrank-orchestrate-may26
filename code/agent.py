import os
import re
from typing import List, Dict

import google.generativeai as genai


def _configure_genai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)


def generate_response(
    issue: str,
    subject: str,
    company: str,
    status: str,
    request_type: str,
    product_area: str,
    retrieved_chunks: List[Dict],
) -> Dict[str, str]:
    """
    Generate a user-facing response and a one-sentence justification using
    Google Gemini (gemini-2.5-pro) constrained to the provided corpus excerpts.

    Returns a dict with keys: "response", "justification".
    """
    _configure_genai()

    # Pick top 3 chunks (preserve order). Each chunk expected to be dict with 'text' and 'source_file'.
    top_chunks = retrieved_chunks[:3]
    excerpts = "\n---\n".join(chunk.get("text", "") for chunk in top_chunks)

    system = (
        "You are a support triage agent. Answer ONLY using the provided support corpus excerpts. "
        "Do not hallucinate policies. Do not invent steps. If the status is \"escalated\", your response must be a polite message "
        "telling the user their issue has been escalated to a human agent and why. If \"replied\", answer directly from the corpus."
    )

    user = (
        f"Company: {company}\n"
        f"Issue: {issue}\n"
        f"Status decided: {status}\n"
        f"Product area: {product_area}\n\n"
        "Relevant corpus excerpts:\n"
        f"{excerpts}"
    )

    prompt = f"System: {system}\n\nUser:\n{user}\n\nRespond in this exact XML format:\n<response>user-facing reply here</response>\n<justification>one sentence explaining routing decision and corpus basis</justification>"

    # Generate with deterministic settings
    try:
        resp = genai.generate(
            model="gemini-2.5-pro",
            prompt=prompt,
            temperature=0,
            max_output_tokens=512,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to call Gemini API: {e}")

    # Extract text from response object (support a couple of possible shapes)
    text = ""
    if isinstance(resp, dict):
        # genai.generate sometimes returns {'candidates': [{'content': '...'}], ...}
        if "candidates" in resp and resp["candidates"]:
            cand = resp["candidates"][0]
            text = cand.get("content") or cand.get("text") or ""
        else:
            text = resp.get("output") or resp.get("text") or ""
    else:
        # fallback for objects with attribute access
        text = getattr(resp, "text", None) or getattr(resp, "output", None) or ""

    if not text:
        # final fallback: string conversion
        text = str(resp)

    # Parse XML tags
    m_resp = re.search(r"<response>(.*?)</response>", text, re.DOTALL | re.IGNORECASE)
    m_just = re.search(r"<justification>(.*?)</justification>", text, re.DOTALL | re.IGNORECASE)

    if not m_resp or not m_just:
        # If strict XML tags not present, attempt to be tolerant: try to split by the tags included literally
        raise ValueError("Gemini output did not contain expected <response> and <justification> tags.\nOutput:\n" + text)

    response_text = m_resp.group(1).strip()
    justification_text = m_just.group(1).strip()

    return {"response": response_text, "justification": justification_text}


if __name__ == "__main__":
    # simple manual test harness (won't run without GEMINI_API_KEY and network)
    try:
        out = generate_response(
            issue="My API key is not working",
            subject="API auth",
            company="Claude",
            status="replied",
            request_type="product_issue",
            product_area="claude-api-and-console",
            retrieved_chunks=[{"text": "Check your API key in the console.", "source_file": "data/claude/claude-api-and-console/api-faq.md"}],
        )
        print(out)
    except Exception as e:
        print("Dry run failed:", e)
