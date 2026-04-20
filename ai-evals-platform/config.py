import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ColumnMapping:
    user_id: str = "user_id"
    session_id: str = "session_id"
    timestamp: str = "timestamp"
    role: str = "role"
    content: str = "message"
    user_role_value: str = "user"
    assistant_role_value: str = "assistant"


@dataclass
class Config:
    redash_url: str = ""
    redash_api_key: str = ""
    anthropic_api_key: str = ""
    model: str = "claude-opus-4-7"
    output_dir: str = "eval_reports"
    max_messages_per_session: int = 50
    column_mapping: ColumnMapping = field(default_factory=ColumnMapping)

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            redash_url=os.environ.get("REDASH_URL", ""),
            redash_api_key=os.environ.get("REDASH_API_KEY", ""),
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        )
