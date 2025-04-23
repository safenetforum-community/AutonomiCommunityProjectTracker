import pytest
from datetime import datetime
from src.models import Repository

@pytest.fixture
def sample_repos():
    return [
        Repository(
            name="Autonomi Network",
            html_url="https://github.com/test/autonomi-network",
            description="Autonomi network implementation",
            updated_at=datetime(2024, 3, 1),
            language="Python",
            stargazers_count=100
        ),
        Repository(
            name="Old Autonomi",
            html_url="https://github.com/test/old-autonomi",
            description="Deprecated Autonomi nodes",
            updated_at=datetime(2023, 12, 1),
            language="JavaScript",
            stargazers_count=50
        ),
        Repository(
            name="Italian Autonomi",
            html_url="https://github.com/test/italian-autonomi",
            description="Rete Autonomi",
            updated_at=datetime(2024, 2, 1),
            language="Italian",
            stargazers_count=30
        )
    ]