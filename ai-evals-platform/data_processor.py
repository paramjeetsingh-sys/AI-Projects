from dataclasses import dataclass, field
from typing import Optional
from config import Config, ColumnMapping


@dataclass
class Message:
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str


@dataclass
class Session:
    session_id: str
    user_id: str
    messages: list[Message] = field(default_factory=list)

    def get_transcript(self, max_messages: Optional[int] = None) -> str:
        msgs = self.messages[-max_messages:] if max_messages else self.messages
        lines = []
        for i, msg in enumerate(msgs, 1):
            role_label = "User" if msg.role == "user" else "AI Assistant"
            lines.append(f"[Turn {i} - {role_label} ({msg.timestamp})]:")
            lines.append(msg.content.strip())
            lines.append("")
        return "\n".join(lines)

    @property
    def user_message_count(self) -> int:
        return sum(1 for m in self.messages if m.role == "user")

    @property
    def ai_message_count(self) -> int:
        return sum(1 for m in self.messages if m.role == "assistant")


@dataclass
class ChatData:
    # {user_id: {session_id: Session}}
    sessions_by_user: dict[str, dict[str, Session]] = field(default_factory=dict)

    def all_sessions(self) -> list[Session]:
        result = []
        for user_sessions in self.sessions_by_user.values():
            result.extend(user_sessions.values())
        return result

    @property
    def total_sessions(self) -> int:
        return sum(len(s) for s in self.sessions_by_user.values())


def _normalize_role(raw_role: str, mapping: ColumnMapping) -> str:
    raw = raw_role.strip().lower()
    if raw in (mapping.user_role_value.lower(), "user", "human", "customer"):
        return "user"
    if raw in (mapping.assistant_role_value.lower(), "assistant", "ai", "bot", "system"):
        return "assistant"
    return raw


def process_csv_rows(rows: list[dict], config: Config) -> ChatData:
    """Parse CSV rows into structured ChatData, grouped by user and session."""
    mapping = config.column_mapping
    chat_data = ChatData()

    for row in rows:
        user_id = str(row.get(mapping.user_id, "unknown")).strip()
        session_id = str(row.get(mapping.session_id, "unknown")).strip()
        timestamp = str(row.get(mapping.timestamp, "")).strip()
        raw_role = str(row.get(mapping.role, "")).strip()

        content_val = row.get(mapping.content, "")
        if not content_val:
            for alt_col in ("content", "message", "text", "response", "body"):
                if alt_col in row and row[alt_col]:
                    content_val = row[alt_col]
                    break

        content = str(content_val).strip()
        if not content:
            continue

        role = _normalize_role(raw_role, mapping)
        msg = Message(timestamp=timestamp, role=role, content=content)

        if user_id not in chat_data.sessions_by_user:
            chat_data.sessions_by_user[user_id] = {}

        if session_id not in chat_data.sessions_by_user[user_id]:
            chat_data.sessions_by_user[user_id][session_id] = Session(
                session_id=session_id, user_id=user_id
            )

        chat_data.sessions_by_user[user_id][session_id].messages.append(msg)

    return chat_data
