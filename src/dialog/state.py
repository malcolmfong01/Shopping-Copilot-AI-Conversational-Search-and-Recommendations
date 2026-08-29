from dataclasses import dataclass, field

ALLOWED_ATTRIBUTES = frozenset({
    "category", "material", "color", "size", "style",
    "brand", "budget", "feature", "use_case", "other",
})


@dataclass
class SessionState:
    session_id: str
    user_profile: dict
    conversation_history: list[dict] = field(default_factory=list)
    constraints: dict[str, str] = field(default_factory=dict)
    attributes_asked: list[str] = field(default_factory=list)
    last_candidates: list[dict] = field(default_factory=list)
    turn: int = 0

    def update(self, user_message: str, turn: int):
        self.turn = turn
        self.conversation_history.append({"role": "user", "content": user_message})

    def add_agent_response(self, message: str, ask_attribute: str | None):
        self.conversation_history.append({"role": "assistant", "content": message})
        if ask_attribute and ask_attribute in ALLOWED_ATTRIBUTES:
            self.attributes_asked.append(ask_attribute)

    def add_constraint(self, attribute: str, value: str, accumulate: bool = False):
        if accumulate and attribute in self.constraints:
            existing = self.constraints[attribute]
            if value.lower() not in existing.lower():
                self.constraints[attribute] = f"{existing}|{value}"
        else:
            self.constraints[attribute] = value

    def flush_constraints(self):
        category = self.constraints.get("category")
        self.constraints = {}
        if category:
            self.constraints["category"] = category
        self.attributes_asked = [a for a in self.attributes_asked if a == "category"]

    def build_query(self) -> str:
        import re
        parts = []
        for attr, val in self.constraints.items():
            cleaned = re.sub(r"^(color|material|budget|size|style|brand):\s*", "", val, flags=re.I)
            if attr == "budget":
                continue
            if attr == "category":
                words = cleaned.split()
                parts.append(" ".join(words[-2:]) if len(words) > 2 else cleaned)
            else:
                sub_parts = cleaned.split("|")
                parts.append(sub_parts[-1].strip())
        if not parts and self.conversation_history:
            parts.append(self.conversation_history[-1]["content"])
        return " ".join(parts)

    def get_unasked_attributes(self) -> list[str]:
        return [a for a in ALLOWED_ATTRIBUTES if a not in self.attributes_asked]

    def get_context_summary(self) -> str:
        lines = []
        if self.user_profile.get("summary"):
            lines.append(f"User: {self.user_profile['summary']}")
        if self.constraints:
            lines.append(f"Known preferences: {self.constraints}")
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            for msg in recent:
                lines.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(lines)


class StateManager:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def reset(self, session_id: str, user_profile: dict) -> SessionState:
        state = SessionState(session_id=session_id, user_profile=user_profile)
        self._sessions[session_id] = state
        return state

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)
