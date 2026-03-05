"""Shared test fixtures."""
import uuid

import pytest


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()
