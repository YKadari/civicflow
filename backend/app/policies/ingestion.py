from sqlalchemy import delete

from app.ai.embeddings import embed_text
from app.database.connection import SessionLocal
from app.database.models import PolicyChunkModel
from app.domain.models import Policy
from app.policies.chunking import chunk_policy


def ingest_policy(
    policy: Policy,
) -> int:

    chunks = chunk_policy(policy)

    with SessionLocal() as session:

        session.execute(
            delete(PolicyChunkModel).where(
                PolicyChunkModel.policy_id
                == policy.policy_id,
                PolicyChunkModel.version
                == policy.version,
            )
        )

        for chunk in chunks:
            embedding = embed_text(
                chunk.content
            )

            db_chunk = PolicyChunkModel(
                chunk_id=chunk.chunk_id,
                policy_id=chunk.policy_id,
                version=chunk.version,
                section=chunk.section,
                content=chunk.content,
                embedding=embedding,
            )

            session.add(db_chunk)

        session.commit()

    return len(chunks)