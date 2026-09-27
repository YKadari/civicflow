from typing import Protocol

from app.domain.models import PolicyEvidence


class PolicyRetriever(Protocol):
    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:
        ...