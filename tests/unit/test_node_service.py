import pytest

from app.models.workflow_node import NodeStatus
from app.services.node_service import InvalidTransition, validate_transition


def test_valid_transitions():
    validate_transition(NodeStatus.PENDING, NodeStatus.READY)
    validate_transition(NodeStatus.READY, NodeStatus.RUNNING)
    validate_transition(NodeStatus.RUNNING, NodeStatus.AWAITING_REVIEW)
    validate_transition(NodeStatus.AWAITING_REVIEW, NodeStatus.APPROVED)
    validate_transition(NodeStatus.AWAITING_REVIEW, NodeStatus.REJECTED)
    validate_transition(NodeStatus.REJECTED, NodeStatus.RUNNING)
    validate_transition(NodeStatus.FAILED, NodeStatus.RUNNING)


def test_invalid_transitions():
    with pytest.raises(InvalidTransition):
        validate_transition(NodeStatus.APPROVED, NodeStatus.RUNNING)

    with pytest.raises(InvalidTransition):
        validate_transition(NodeStatus.PENDING, NodeStatus.RUNNING)

    with pytest.raises(InvalidTransition):
        validate_transition(NodeStatus.SKIPPED, NodeStatus.RUNNING)
