from typing import Protocol

from app.ai.models import (
    GroundedRecommendation,
    IntentClassification,
)


class AIProvider(Protocol):
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:
        ...

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[dict],
    ) -> GroundedRecommendation:
        ...