from app.policies.base import PolicyRetriever
from app.policies.retrieval import (
    PgVectorPolicyRetriever,
)


def get_policy_retriever() -> PolicyRetriever:
    return PgVectorPolicyRetriever()