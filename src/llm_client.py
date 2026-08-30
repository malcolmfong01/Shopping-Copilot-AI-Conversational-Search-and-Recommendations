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


def _groq_call(prompt: str, max_tokens: int, temperature: float, api_key: str) -> str | None:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort="low",
        )
        print("### RAW GROQ RESPONSE:", response.choices[0].message, flush=True)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("### GROQ CALL FAILED:", repr(e), flush=True)
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
