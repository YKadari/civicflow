from typing import Protocol

from app.ai.models import IntentClassification


class AIProvider(Protocol):
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:
        ...