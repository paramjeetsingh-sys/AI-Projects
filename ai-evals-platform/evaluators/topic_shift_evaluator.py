from data_processor import Session
from .base_evaluator import BaseEvaluator, EvalScore

TOPIC_SHIFT_PROMPT = """\
Analyze the following AI conversation for TOPIC SHIFTING ability when users give repetitive responses.

WHAT TO LOOK FOR — Repetition Patterns:
- User sends nearly identical messages multiple times (same words/phrases)
- User keeps returning to the same topic/complaint without resolution
- User gives the same short non-committal answer repeatedly (e.g., "ok", "yes", "I don't know")
- User seems stuck in a conversational loop with no progression
- Conversation stagnates with the AI asking the same type of question repeatedly

EVALUATION CRITERIA:
1. Does the AI detect when the user is giving repetitive responses?
2. Does the AI proactively introduce new angles, topics, or perspectives?
3. Is the topic shift natural and organic (not abrupt or dismissive)?
4. Does the new topic/angle successfully re-engage the user?
5. Does the AI vary its communication style when repetition is detected?

EFFECTIVE TOPIC SHIFT TECHNIQUES:
- Reframing the same topic from a different angle
- Introducing a related but fresh topic that connects to user interests
- Asking a completely different type of question (e.g., switching from informational to personal)
- Using storytelling or examples to break the pattern
- Acknowledging the repetition and explicitly pivoting

SCORING GUIDE (0-10):
- 9-10: Expertly detects repetition and pivots elegantly; user becomes re-engaged
- 7-8: Usually shifts topics well; occasional missed opportunities
- 5-6: Sometimes shifts topics but timing/execution is inconsistent
- 3-4: Rarely shifts topics; conversation gets stuck in loops
- 0-2: Never adapts; conversation completely stagnates when repetition occurs
- N/A (score: -1): No repetition detected in this conversation

CONVERSATION TRANSCRIPT:
---
{transcript}
---

Return ONLY this JSON (no other text):
{{
  "score": <number 0-10, or -1 if no repetition detected>,
  "repetition_instances": <integer count of detected repetition patterns>,
  "shift_attempts": <integer count of AI topic shift attempts>,
  "successful_shifts": <integer count of successful re-engagement shifts>,
  "repeated_patterns": ["description of repetition pattern found", ...],
  "issues": ["specific missed opportunity or poor shift with quoted example", ...],
  "highlights": ["effective topic shift technique with quoted example", ...],
  "explanation": "2-3 sentence overall topic shifting assessment"
}}"""


class TopicShiftEvaluator(BaseEvaluator):
    def evaluate(self, session: Session) -> EvalScore:
        if session.user_message_count < 3:
            return EvalScore(
                score=-1.0,
                explanation="Too few user messages to assess topic shifting.",
                extra={"repetition_instances": 0, "shift_attempts": 0, "successful_shifts": 0},
            )

        transcript = self._format_transcript(session)
        prompt = TOPIC_SHIFT_PROMPT.format(transcript=transcript)
        data = self._call_claude(prompt)

        raw_score = float(data.get("score", -1))
        return EvalScore(
            score=raw_score,
            issues=data.get("issues", []),
            highlights=data.get("highlights", []),
            explanation=data.get("explanation", ""),
            extra={
                "repetition_instances": data.get("repetition_instances", 0),
                "shift_attempts": data.get("shift_attempts", 0),
                "successful_shifts": data.get("successful_shifts", 0),
                "repeated_patterns": data.get("repeated_patterns", []),
            },
        )
