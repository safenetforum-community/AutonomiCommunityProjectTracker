from src.scraper import search_repos
from datetime import datetime


def format_date(dt):
    return dt.strftime('%Y-%m-%d')


if __name__ == "__main__":
    print("Searching for Autonomi repositories...\n")
    results = search_repos()

    print(f"Found {len(results)} matching repositories:\n")
    for i, repo in enumerate(results, 1):
        print(f"{i}. {repo.name}")
        print(f"   URL: {repo.html_url}")
        print(f"   Language: {repo.language or 'Not specified'}")
        print(f"   Last updated: {format_date(repo.updated_at)}")
        print(f"   Stars: {repo.stargazers_count}")
        print(f"   Description: {repo.description[:100]}...\n")
