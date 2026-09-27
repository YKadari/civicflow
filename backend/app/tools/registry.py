from dataclasses import dataclass
from typing import Callable, Literal

from app.domain.models import ActionType
from app.tools.payments import check_payment


ToolAccessMode = Literal[
    "read_only",
    "state_changing",
]


@dataclass(frozen=True)
class ToolDefinition:
    action: ActionType
    name: str
    access_mode: ToolAccessMode
    requires_approval: bool
    handler: Callable | None = None


TOOL_REGISTRY: dict[
    ActionType,
    ToolDefinition,
] = {
    ActionType.CHECK_PAYMENT: ToolDefinition(
        action=ActionType.CHECK_PAYMENT,
        name="check_payment",
        access_mode="read_only",
        requires_approval=False,
        handler=check_payment,
    ),

    ActionType.OPEN_INVESTIGATION: ToolDefinition(
        action=ActionType.OPEN_INVESTIGATION,
        name="open_investigation",
        access_mode="state_changing",
        requires_approval=True,
    ),

    ActionType.REQUEST_DOCUMENT: ToolDefinition(
        action=ActionType.REQUEST_DOCUMENT,
        name="request_document",
        access_mode="state_changing",
        requires_approval=True,
    ),

    ActionType.UPDATE_CONTACT_INFO: ToolDefinition(
        action=ActionType.UPDATE_CONTACT_INFO,
        name="update_contact_info",
        access_mode="state_changing",
        requires_approval=True,
    ),

    ActionType.CLOSE_CASE: ToolDefinition(
        action=ActionType.CLOSE_CASE,
        name="close_case",
        access_mode="state_changing",
        requires_approval=True,
    ),
}


def get_tool_definition(
    action: ActionType,
) -> ToolDefinition | None:

    return TOOL_REGISTRY.get(action)