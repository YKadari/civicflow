from datetime import date
from pathlib import Path

from app.domain.models import Policy


POLICY_DIRECTORY = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "policies"
)


def load_policy(
    file_name: str,
    policy_id: str,
    title: str,
    version: int,
    effective_date: date,
) -> Policy:

    file_path = POLICY_DIRECTORY / file_name

    content = file_path.read_text(
        encoding="utf-8"
    )

    return Policy(
        policy_id=policy_id,
        title=title,
        version=version,
        effective_date=effective_date,
        content=content,
    )