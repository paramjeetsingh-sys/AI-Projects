import sys
from dataclasses import dataclass, field
from typing import Optional
from data_processor import ChatData, Session
from evaluators import AccuracyEvaluator, EngagementEvaluator, TopicShiftEvaluator
from evaluators.base_evaluator import EvalScore
from config import Config


@dataclass
class SessionResult:
    user_id: str
    session_id: str
    message_count: int
    user_message_count: int
    ai_message_count: int
    accuracy: Optional[EvalScore] = None
    engagement: Optional[EvalScore] = None
    topic_shift: Optional[EvalScore] = None
    error: Optional[str] = None

    @property
    def overall_score(self) -> float:
        """Average of available scored evaluations (topic shift -1 means N/A)."""
        scores = []
        if self.accuracy:
            scores.append(self.accuracy.score)
        if self.engagement:
            scores.append(self.engagement.score)
        if self.topic_shift and self.topic_shift.score >= 0:
            scores.append(self.topic_shift.score)
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    def to_dict(self) -> dict:
        def score_to_dict(s: Optional[EvalScore]) -> Optional[dict]:
            if not s:
                return None
            return {
                "score": s.score,
                "issues": s.issues,
                "highlights": s.highlights,
                "explanation": s.explanation,
                "extra": s.extra,
            }

        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "message_count": self.message_count,
            "user_message_count": self.user_message_count,
            "ai_message_count": self.ai_message_count,
            "overall_score": self.overall_score,
            "accuracy": score_to_dict(self.accuracy),
            "engagement": score_to_dict(self.engagement),
            "topic_shift": score_to_dict(self.topic_shift),
            "error": self.error,
        }


class EvalRunner:
    def __init__(self, config: Config):
        self.config = config
        self.accuracy_eval = AccuracyEvaluator(config)
        self.engagement_eval = EngagementEvaluator(config)
        self.topic_shift_eval = TopicShiftEvaluator(config)

    def run_session(self, session: Session) -> SessionResult:
        result = SessionResult(
            user_id=session.user_id,
            session_id=session.session_id,
            message_count=len(session.messages),
            user_message_count=session.user_message_count,
            ai_message_count=session.ai_message_count,
        )

        if len(session.messages) < 2:
            result.error = "Session too short (< 2 messages)"
            return result

        try:
            result.accuracy = self.accuracy_eval.evaluate(session)
        except Exception as e:
            result.error = f"Accuracy eval failed: {e}"

        try:
            result.engagement = self.engagement_eval.evaluate(session)
        except Exception as e:
            if result.error:
                result.error += f"; Engagement eval failed: {e}"
            else:
                result.error = f"Engagement eval failed: {e}"

        try:
            result.topic_shift = self.topic_shift_eval.evaluate(session)
        except Exception as e:
            if result.error:
                result.error += f"; Topic shift eval failed: {e}"
            else:
                result.error = f"Topic shift eval failed: {e}"

        return result

    def run_all(
        self, chat_data: ChatData, limit: Optional[int] = None, verbose: bool = True
    ) -> list[SessionResult]:
        sessions = chat_data.all_sessions()
        if limit:
            sessions = sessions[:limit]

        total = len(sessions)
        results = []

        for i, session in enumerate(sessions, 1):
            if verbose:
                print(
                    f"  [{i}/{total}] Evaluating session {session.session_id} "
                    f"(user={session.user_id}, {len(session.messages)} messages)...",
                    flush=True,
                )

            result = self.run_session(session)
            results.append(result)

            if verbose and result.error:
                print(f"    WARNING: {result.error}", file=sys.stderr)
            elif verbose:
                acc = f"{result.accuracy.score:.1f}" if result.accuracy else "N/A"
                eng = f"{result.engagement.score:.1f}" if result.engagement else "N/A"
                ts_score = result.topic_shift.score if result.topic_shift else None
                ts = f"{ts_score:.1f}" if ts_score is not None and ts_score >= 0 else "N/A"
                print(
                    f"    accuracy={acc}/10  engagement={eng}/10  topic_shift={ts}/10  "
                    f"overall={result.overall_score:.1f}/10"
                )

        return results
