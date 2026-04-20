from data_processor import Session
from .base_evaluator import BaseEvaluator, EvalScore

ENGAGEMENT_PROMPT = """\
Analyze the following AI conversation for USER ENGAGEMENT quality.

Evaluate whether the AI assistant:
1. Uses a warm, conversational tone that invites continued dialogue
2. Asks thoughtful follow-up questions to understand the user better
3. Builds on previous user responses rather than treating each message in isolation
4. Provides responses with enough depth to sustain interest (not too brief, not overwhelming)
5. Shows genuine curiosity about the user's situation and goals
6. Creates moments that make the user want to share more

ENGAGEMENT SIGNALS TO LOOK FOR:
- User gives longer responses over time (increasing engagement)
- User answers follow-up questions enthusiastically
- User volunteers extra information beyond what was asked
- User asks their own follow-up questions back
- Conversation has natural back-and-forth flow

DISENGAGEMENT SIGNALS:
- User gives one-word or very short answers
- User stops asking questions or sharing details
- Conversation dies after few turns
- User seems to just be going through the motions

SCORING GUIDE (0-10):
- 9-10: Highly engaging; user is clearly invested, conversation flows naturally
- 7-8: Good engagement; mostly active user with occasional lulls
- 5-6: Moderate engagement; conversation is functional but not compelling
- 3-4: Poor engagement; user seems disinterested, minimal participation
- 0-2: No meaningful engagement; one-word responses, conversation dies quickly

CONVERSATION TRANSCRIPT:
---
{transcript}
---

Return ONLY this JSON (no other text):
{{
  "score": <number 0-10>,
  "issues": ["specific engagement problem with quoted example", ...],
  "highlights": ["effective engagement technique with quoted example", ...],
  "explanation": "2-3 sentence overall engagement assessment"
}}"""


class EngagementEvaluator(BaseEvaluator):
    def evaluate(self, session: Session) -> EvalScore:
        if session.user_message_count < 2:
            return EvalScore(
                score=5.0,
                explanation="Too few user messages to assess engagement.",
            )

        transcript = self._format_transcript(session)
        prompt = ENGAGEMENT_PROMPT.format(transcript=transcript)
        data = self._call_claude(prompt)

        return EvalScore(
            score=float(data.get("score", 0)),
            issues=data.get("issues", []),
            highlights=data.get("highlights", []),
            explanation=data.get("explanation", ""),
        )
