import pytest

from scripts.seed_database import seed_database


@pytest.fixture
def seeded_database():
    seed_database()

    yield

    seed_database()