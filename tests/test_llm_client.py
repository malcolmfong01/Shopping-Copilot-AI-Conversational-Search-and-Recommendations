import src.llm_client as llm_client


def test_llm_call_prefers_groq_when_both_keys_set(monkeypatch):
    calls = []

    def fake_groq(prompt, max_tokens, temperature, api_key):
        calls.append(("groq", api_key))
        return "ok"

    def fake_gemini(prompt, max_tokens, temperature, api_key):
        calls.append(("gemini", api_key))
        return "gemini"

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("GOOGLE_API_KEY", "google_test")
    monkeypatch.setattr(llm_client, "_groq_call", fake_groq)
    monkeypatch.setattr(llm_client, "_gemini_call", fake_gemini)

    assert llm_client.llm_call("hello") == "ok"
    assert calls == [("groq", "gsk_test")]
