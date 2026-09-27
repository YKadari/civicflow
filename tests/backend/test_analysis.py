import pytest

from app.ai.models import IntentClassification
from app.services.analysis import analyze_case_request
from app.ai.exceptions import AIProviderError

pytestmark = pytest.mark.usefixtures(
    "seeded_database"
)
class BrokenAIProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        raise AIProviderError(
            "AI unavailable"
        )
def test_ai_failure_uses_fallback():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=BrokenAIProvider(),
    )

    assert analysis is not None

    assert (
        analysis.classification_source
        == "fallback"
    )

    assert analysis.requires_human_review is True

    assert analysis.recommended_action is None
class LowConfidenceProvider:
    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:

        return IntentClassification(
            request_type="payment_issue",
            confidence=0.40,
        )


def test_low_confidence_requires_review():
    analysis = analyze_case_request(
        case_id="CF-10001",
        event_id="EVT-10001-1",
        ai_provider=LowConfidenceProvider(),
    )

    assert analysis is not None

    assert analysis.request_type == "payment_issue"

    assert analysis.requires_human_review is True

    assert analysis.recommended_action is None