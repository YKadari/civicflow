import os

from dotenv import load_dotenv
from sqlalchemy import select

from app.ai.embeddings import embed_text
from app.database.connection import SessionLocal
from app.database.models import PolicyChunkModel
from app.domain.models import PolicyEvidence


load_dotenv()


POLICY_SIMILARITY_THRESHOLD = float(
    os.getenv(
        "POLICY_SIMILARITY_THRESHOLD",
        "0.45",
    )
)


class PgVectorPolicyRetriever:
    def retrieve(
        self,
        query: str,
        limit: int = 3,
    ) -> list[PolicyEvidence]:

        query_embedding = embed_text(query)

        distance = (
            PolicyChunkModel.embedding
            .cosine_distance(query_embedding)
        )

        statement = (
            select(
                PolicyChunkModel,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(limit)
        )

        with SessionLocal() as session:
            results = session.execute(
                statement
            ).all()

        evidence = []

        for db_chunk, cosine_distance in results:
            similarity = (
                1.0 - float(cosine_distance)
            )

            if (
                similarity
                < POLICY_SIMILARITY_THRESHOLD
            ):
                continue

            evidence.append(
                PolicyEvidence(
                    chunk_id=db_chunk.chunk_id,
                    policy_id=db_chunk.policy_id,
                    version=db_chunk.version,
                    section=db_chunk.section,
                    content=db_chunk.content,
                    similarity=similarity,
                )
            )

        return evidence