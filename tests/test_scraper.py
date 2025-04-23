import pytest
from datetime import datetime
from src.scraper import filter_by_date, filter_by_language
from src.models import Repository


def test_filter_by_date(sample_repos):
    filtered = filter_by_date(sample_repos)
    assert len(filtered) == 2
    assert all(repo.updated_at.year == 2024 for repo in filtered)


def test_filter_by_language(sample_repos):
    filtered = filter_by_language(sample_repos)
    assert len(filtered) == 2
    assert all(repo.language != 'Italian' for repo in filtered)


def test_combined_filters(sample_repos):
    date_filtered = filter_by_date(sample_repos)
    both_filtered = filter_by_language(date_filtered)
    assert len(both_filtered) == 1
    assert both_filtered[0].name == "Autonomi Network"
