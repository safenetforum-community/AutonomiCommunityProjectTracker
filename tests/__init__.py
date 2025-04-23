"""
Test package for Autonomi Repository Scraper.

This package contains all unit and integration tests for the GitHub repository scraper.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "test_data"


def pytest_configure(config):
    """Pytest configuration hook."""
    # Create test data directory if it doesn't exist
    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Set environment variables for testing
    os.environ["TESTING"] = "1"

    if not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = "mock_token_for_testing"


# Import fixtures to make them available to all tests
from .conftest import sample_repos  # noqa: F401

__all__ = [
    'TEST_DATA_DIR',
    'pytest_configure'
]
