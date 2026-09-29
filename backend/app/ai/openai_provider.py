import os
from typing import Any, TypeVar

import openai
from openai import OpenAI
from pydantic import BaseModel

from app.ai.exceptions import AIProviderError
from app.ai.models import (
    DecisionChallengeResult,
    GroundedRecommendation,
    IntentClassification,
)


T = TypeVar(
    "T",
    bound=BaseModel,
)


class OpenAIProvider:
    """
    Cloud AI provider for CivicFlow.

    The local development path continues to use Ollama.
    This provider is used only when AI_PROVIDER=openai.
    """

    def __init__(
        self,
        model: str | None = None,
        client: Any | None = None,
    ):
        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-6-luna",
            )
        )

        self.client = (
            client
            if client is not None
            else OpenAI()
        )

    def _parse_response(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=response_model,
            )

        except openai.APIError as exc:
            raise AIProviderError(
                "OpenAI API request failed."
            ) from exc

        parsed = response.output_parsed

        if parsed is None:
            raise AIProviderError(
                "OpenAI did not return a valid structured response."
            )

        return parsed

    @staticmethod
    def _evidence_value(
        item: Any,
        field: str,
    ) -> Any:
        """
        Supports either dictionaries or CivicFlow policy
        evidence objects.
        """
        if isinstance(item, dict):
            return item.get(field)

        return getattr(
            item,
            field,
            None,
        )

    def _format_policy_evidence(
        self,
        policy_evidence: list[Any],
    ) -> str:
        if not policy_evidence:
            return "No policy evidence supplied."

        sections: list[str] = []

        for item in policy_evidence:
            chunk_id = self._evidence_value(
                item,
                "chunk_id",
            )
            policy_id = self._evidence_value(
                item,
                "policy_id",
            )
            version = self._evidence_value(
                item,
                "version",
            )
            section = self._evidence_value(
                item,
                "section",
            )
            content = self._evidence_value(
                item,
                "content",
            )

            sections.append(
                (
                    f"Chunk ID: {chunk_id}\n"
                    f"Policy: {policy_id}\n"
                    f"Version: {version}\n"
                    f"Section: {section}\n"
                    f"Content: {content}"
                )
            )

        return "\n\n".join(
            sections
        )

    def classify_intent(
        self,
        description: str,
    ) -> IntentClassification:
        system_prompt = """
You classify citizen requests for CivicFlow, a
public-service case-management system.

Choose the most appropriate request type from the
schema you were given.

Do not invent facts.

Return only the requested structured result.
""".strip()

        user_prompt = f"""
Citizen request:

{description}
""".strip()

        return self._parse_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=IntentClassification,
        )

    def recommend_action(
        self,
        case_id: str,
        request_description: str,
        facts: list[str],
        policy_evidence: list[Any],
    ) -> GroundedRecommendation:
        facts_text = (
            "\n".join(
                f"- {fact}"
                for fact in facts
            )
            or "No case facts supplied."
        )

        policy_text = (
            self._format_policy_evidence(
                policy_evidence
            )
        )

        system_prompt = """
        You assist a public-service caseworker in CivicFlow.

        Recommend an action using ONLY the supplied case facts
        and policy evidence.

        Available actions:

        - check_payment
        - open_investigation
        - request_document
        - update_contact_info
        - close_case
        - none

        ACTION SELECTION RULES:

        1. Prefer the least consequential action that directly
        addresses the citizen's request.

        2. Use check_payment when the citizen is asking:
        - where a payment is
        - whether a payment was sent
        - why a payment has not arrived
        - what the current payment status is
        - to check what happened to a payment

        check_payment is a read-only status lookup and does
        NOT require the prerequisites for opening an
        investigation.

        3. Use open_investigation when the citizen explicitly
        requests:
        - an investigation
        - a formal investigation
        - an escalation into the missing payment
        - an investigation workflow

        If the retrieved policy establishes that an
        investigation pathway exists, you may recommend
        open_investigation even when some prerequisite facts
        are missing or uncertain.

        Do NOT invent those missing facts.

        Clearly identify uncertainty in the rationale.
        CivicFlow's deterministic policy gate and independent
        Decision Challenge will decide whether the proposed
        investigation is actually allowed to proceed.

        4. Do not replace an explicit investigation request with
        check_payment merely because a prerequisite fact is
        missing. Missing prerequisites should be surfaced for
        downstream safety checks.

        5. Use request_document only when the citizen's request,
        case facts, and retrieved policy make document
        collection the appropriate proposed action.

        6. Use update_contact_info when the citizen requests a
        contact-information change.

        7. Use close_case only when the citizen or case context
        clearly concerns closure and retrieved policy provides
        a relevant closure pathway.

        8. Use none when no available action is relevant or
        supported by the retrieved policy.

        GROUNDING RULES:

        - Do not invent policy.
        - Do not invent case facts.
        - Cite only policy chunk IDs supplied in the prompt.
        - Preserve policy language such as "may", "should",
        and "must".
        - A recommendation is NOT authorization.
        - CivicFlow applies deterministic checks, an independent
        Decision Challenge, tool permissions, and human review
        after this recommendation.

        Return only the requested structured result.
        """.strip()

        user_prompt = f"""
CASE ID:
{case_id}

CITIZEN REQUEST:
{request_description}

CASE FACTS:
{facts_text}

POLICY EVIDENCE:
{policy_text}
""".strip()

        return self._parse_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=GroundedRecommendation,
        )

    def challenge_decision(
        self,
        case_id: str,
        proposed_action: str,
        facts: list[str],
        policy_evidence: list[Any],
    ) -> DecisionChallengeResult:
        """
        Independently challenge a consequential action.

        The recommendation rationale is intentionally not
        provided so the challenger is less anchored to the
        original model's reasoning.
        """

        facts_text = (
            "\n".join(
                f"- {fact}"
                for fact in facts
            )
            or "No case facts supplied."
        )

        policy_text = (
            self._format_policy_evidence(
                policy_evidence
            )
        )

        system_prompt = """
You are CivicFlow's independent Decision Challenge
reviewer.

Another process has proposed a consequential action.

Your job is not to defend the proposed action.
Actively look for a material reason that it should
not proceed.

Use ONLY the supplied case facts and policy evidence.

Look for:

- required facts that are missing
- timing requirements that have not been established
- contradictions with policy
- eligibility or verification problems
- unsupported assumptions
- differences between "may", "should", and "must"
- evidence that the proposed action is premature
- situations that require human review

Rules:

1. Do not invent case facts.
2. Do not invent policy.
3. Cite only policy chunk IDs supplied to you.
4. If a material required fact is missing, challenge
   the action.
5. Pass the action only when you cannot identify a
   material policy or evidence problem.
6. The fact that another model recommended the action
   is not evidence that the action is correct.

Return only the requested structured result.
""".strip()

        user_prompt = f"""
CASE ID:
{case_id}

PROPOSED ACTION:
{proposed_action}

CASE FACTS:
{facts_text}

POLICY EVIDENCE:
{policy_text}
""".strip()

        return self._parse_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=DecisionChallengeResult,
        )