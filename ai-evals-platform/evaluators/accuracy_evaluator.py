from data_processor import Session
from .base_evaluator import BaseEvaluator, EvalScore

ACCURACY_PROMPT = """\
Analyze the following AI conversation for RESPONSE ACCURACY.

Evaluate whether the AI assistant:
1. Provides factually correct, verifiable information
2. Gives responses directly relevant to what the user asked
3. Avoids hallucinations, fabrications, or made-up details
4. Acknowledges uncertainty rather than guessing incorrectly
5. Stays consistent throughout the conversation (no contradictions)
6. Addresses all parts of multi-part user questions

SCORING GUIDE (0-10):
- 9-10: All responses are accurate, relevant, and complete
- 7-8: Mostly accurate; minor irrelevance or slight omissions
- 5-6: Several inaccuracies or frequently off-topic responses
- 3-4: Many inaccuracies; significant relevance problems
- 0-2: Severely inaccurate, hallucinating, or completely irrelevant

CONVERSATION TRANSCRIPT:
---
{transcript}
---

Return ONLY this JSON (no other text):
{{
  "score": <number 0-10>,
  "issues": ["specific accuracy problem with quoted example", ...],
  "highlights": ["specific accurate/relevant response with quoted example", ...],
  "explanation": "2-3 sentence overall accuracy assessment"
}}"""


class AccuracyEvaluator(BaseEvaluator):
    def evaluate(self, session: Session) -> EvalScore:
        if session.ai_message_count == 0:
            return EvalScore(score=0.0, explanation="No AI messages found in session.")

        transcript = self._format_transcript(session)
        prompt = ACCURACY_PROMPT.format(transcript=transcript)
        data = self._call_claude(prompt)

        return EvalScore(
            score=float(data.get("score", 0)),
            issues=data.get("issues", []),
            highlights=data.get("highlights", []),
            explanation=data.get("explanation", ""),
        )
