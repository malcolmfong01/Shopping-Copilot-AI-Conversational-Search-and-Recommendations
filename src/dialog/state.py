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

    def add_constraint(self, attribute: str, value: str):
        self.constraints[attribute] = value

    def flush_constraints(self):
        self.constraints = {}
        self.attributes_asked = []

    def build_query(self) -> str:
        parts = []
        if self.conversation_history:
            last_msg = self.conversation_history[-1]["content"]
            parts.append(last_msg)
        for attr, val in self.constraints.items():
            parts.append(f"{attr}: {val}")
        profile_tags = self.user_profile.get("preference_tags", [])
        if profile_tags and self.turn <= 2:
            parts.extend(profile_tags[:3])
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
