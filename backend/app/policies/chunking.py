from dataclasses import dataclass

from app.domain.models import Policy


@dataclass
class PolicyChunk:
    chunk_id: str
    policy_id: str
    version: int
    section: str
    content: str


def chunk_policy(
    policy: Policy,
) -> list[PolicyChunk]:

    chunks = []

    current_section = None
    current_lines = []

    def save_chunk():
        if current_section is None:
            return

        content = "\n".join(
            current_lines
        ).strip()

        if not content:
            return

        section_key = (
            current_section
            .split()[0]
            .replace(".", "_")
        )

        chunks.append(
            PolicyChunk(
                chunk_id=(
                    f"{policy.policy_id}"
                    f"-V{policy.version}"
                    f"-{section_key}"
                ),
                policy_id=policy.policy_id,
                version=policy.version,
                section=current_section,
                content=content,
            )
        )

    for line in policy.content.splitlines():

        if line.startswith("## "):
            save_chunk()

            current_section = line[3:].strip()
            current_lines = []

        elif current_section is not None:
            current_lines.append(line)

    save_chunk()

    return chunks