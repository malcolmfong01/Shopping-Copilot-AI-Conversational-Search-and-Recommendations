"""Provider-agnostic LLM client. Supports Google Gemini (free) and Groq (free).

Usage:
    from src.llm_client import llm_call

    response = llm_call("Your prompt here", max_tokens=200)

Set one of these environment variables (checked in this order):
    GOOGLE_API_KEY=...         (Google Gemini Flash — primary, higher rate limits)
    GROQ_API_KEY=gsk_...       (Groq Llama 3.3 70B — fallback)

If neither is set, returns None (modules fall back to heuristics).
"""

import os


def llm_call(prompt: str, max_tokens: int = 200, temperature: float = 0.0) -> str | None:
    """Make a single LLM call. Returns response text or None if no provider available."""
    groq_key = os.environ.get("GROQ_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")

    if groq_key:
        return _groq_call(prompt, max_tokens, temperature, groq_key)
    elif google_key:
        return _gemini_call(prompt, max_tokens, temperature, google_key)
    return None


def _extract_text_from_message(message: object) -> str | None:
    if message is None:
        return None

    content = getattr(message, "content", None)
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text") or part.get("content") or ""
            else:
                text = str(part)
            if text:
                parts.append(str(text))
        content = "".join(parts)

    if isinstance(content, str) and content.strip():
        return content.strip()

    reasoning = getattr(message, "reasoning", None)
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    output_text = getattr(message, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    return None


def _groq_call(prompt: str, max_tokens: int, temperature: float, api_key: str) -> str | None:
    try:
        from groq import Groq

        reasoning_effort = os.environ.get("GROQ_REASONING_EFFORT", "medium").strip().lower()
        if reasoning_effort not in {"low", "medium", "high"}:
            reasoning_effort = "medium"

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

        message = response.choices[0].message
        text = _extract_text_from_message(message)
        if text:
            return text

        raw = getattr(response, "output_text", None)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()

        return None
    except Exception:
        return None


def _gemini_call(prompt: str, max_tokens: int, temperature: float, api_key: str) -> str | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.6-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return response.text.strip()
    except Exception:
        return None
