from src.dialog.state import SessionState


def detect_intent_override(state: SessionState, user_message: str) -> bool:
    """Check if the user's message contradicts accumulated constraints.

    Returns True if the user appears to have changed their mind.
    This is a rule-based heuristic; Yanyox may replace with LLM-based detection.
    """
    if state.turn < 3 or not state.constraints:
        return False

    override_signals = [
        "actually",
        "instead",
        "never mind",
        "changed my mind",
        "forget that",
        "something else",
        "different",
        "not anymore",
        "on second thought",
    ]

    msg_lower = user_message.lower()
    has_signal = any(signal in msg_lower for signal in override_signals)
    if not has_signal:
        return False

    for attr, value in state.constraints.items():
        negation_patterns = [
            f"not {value.lower()}",
            f"no {value.lower()}",
            f"don't want {value.lower()}",
            f"instead of {value.lower()}",
        ]
        if any(pat in msg_lower for pat in negation_patterns):
            return True

    return False
