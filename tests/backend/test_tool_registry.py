from app.domain.models import ActionType
from app.tools.registry import (
    get_tool_definition,
)


def test_check_payment_is_read_only():
    tool = get_tool_definition(
        ActionType.CHECK_PAYMENT
    )

    assert tool is not None

    assert (
        tool.name
        == "check_payment"
    )

    assert (
        tool.access_mode
        == "read_only"
    )

    assert (
        tool.requires_approval
        is False
    )

    assert tool.handler is not None


def test_close_case_requires_approval():
    tool = get_tool_definition(
        ActionType.CLOSE_CASE
    )

    assert tool is not None

    assert (
        tool.access_mode
        == "state_changing"
    )

    assert (
        tool.requires_approval
        is True
    )


def test_request_document_requires_approval():
    tool = get_tool_definition(
        ActionType.REQUEST_DOCUMENT
    )

    assert tool is not None

    assert (
        tool.requires_approval
        is True
    )