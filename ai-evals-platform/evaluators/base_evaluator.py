import json
import re
import anthropic
from dataclasses import dataclass, field
from data_processor import Session
from config import Config


@dataclass
class EvalScore:
    score: float  # 0-10
    issues: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    explanation: str = ""
    extra: dict = field(default_factory=dict)


SHARED_EVALUATOR_CONTEXT = """\
You are an expert AI conversation quality evaluator with deep expertise in:
- Conversational AI assessment and benchmarking
- Natural language understanding and generation quality
- User experience and engagement metrics
- AI safety and helpfulness evaluation

You analyze real conversations between users and AI assistants.
Your evaluations are objective, evidence-based, and actionable.
You always cite specific examples from the conversation to support your scores.

IMPORTANT: You must respond with ONLY valid JSON — no preamble, no markdown code blocks, no extra text.
The JSON must exactly match the schema provided in each evaluation request."""


class BaseEvaluator:
    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self.model = config.model

    def _call_claude(self, user_prompt: str) -> dict:
        """Call Claude with the shared cached system prompt and parse JSON response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SHARED_EVALUATOR_CONTEXT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from response (thinking blocks are skipped)
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content = block.text
                break

        return self._parse_json(text_content)

    def _parse_json(self, text: str) -> dict:
        """Parse JSON from Claude's response, handling common formatting issues."""
        text = text.strip()

        # Strip markdown code blocks if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return json.loads(text.strip())

    def _format_transcript(self, session: Session) -> str:
        return session.get_transcript(
            max_messages=self.config.max_messages_per_session
        )
