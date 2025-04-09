import requests
from datetime import datetime, timedelta
import os
import re
import argparse

# GitHub API setup
GITHUB_API_URL = "https://api.github.com/search/repositories"
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'} if TOKEN else {}

# Configuration
REQUEST_DELAY = 2
MIN_START_DATE = "2024-01-01"
TRACKER_REPO = "AutonomiCommunityProjectTracker"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recent', action='store_true',
                      help='Only show projects updated in the last week')
    parser.add_argument('--debug', action='store_true',
                      help='Show debug information')
    return parser.parse_args()

def search_repositories(args):
    """Search for exact 'Autonomi' matches in description"""
    exact_phrases = [
        '"Autonomi"',  # Exact phrase match
        '"autonomi"',
        '"Autonomi Network"',
        '"autonomi network"',
        '"Safe Network"',
        '"safe network"',
        '"maidsafe"'
    ]
    
    if args.recent:
        last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_filter = f" updated:>{last_week}"
    else:
        date_filter = ""
    
    repos = []
    for phrase in exact_phrases:
        query = f"{phrase} in:description created:>{MIN_START_DATE}{date_filter}"
        try:
            response = requests.get(
                GITHUB_API_URL,
                headers=HEADERS,
                params={
                    'q': query,
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': 100
                }
            )
            response.raise_for_status()
            repos.extend(response.json().get('items', []))
            
            if args.debug:
                print(f"DEBUG: Search '{query}' found {len(response.json().get('items', []))} results")
        except Exception as e:
            if args.debug:
                print(f"DEBUG: Error searching '{query}': {str(e)}")
            continue
    
    # Always include the tracker itself
    tracker_query = f"{TRACKER_REPO} in:name"
    try:
        response = requests.get(
            GITHUB_API_URL,
            headers=HEADERS,
            params={
                'q': tracker_query,
                'per_page': 1
            }
        )
        response.raise_for_status()
        if response.json().get('items'):
            repos.extend(response.json().get('items'))
    except Exception as e:
        if args.debug:
            print(f"DEBUG: Error searching tracker: {str(e)}")
    
    return repos

def is_autonomi_project(repo):
    """Strict verification of Autonomi references"""
    description = repo.get('description', '').lower()
    return any(
        re.search(rf'\b{term}\b', description)
        for term in ['autonomi', 'safe network', 'maidsafe']
    )

def generate_report(repos, args):
    """Generate filtered report with strict matching"""
    markdown = f"""# Autonomi Community Project Tracker
### (Created after {MIN_START_DATE}{' and updated in last week' if args.recent else ''})

| Repository | Description | Updated | Stars |
|------------|-------------|---------|-------|
"""
    count = 0
    for repo in repos:
        if not is_autonomi_project(repo):
            if args.debug:
                print(f"DEBUG: Skipping {repo['full_name']} - no Autonomi reference")
            continue
            
        description = repo.get('description', '')
        markdown += f"""| [{repo['full_name']}]({repo['html_url']}) | {description} | {repo['updated_at'][:10]} | {repo['stargazers_count']} |
"""
        count += 1
    
    if count == 0:
        markdown += "| No matching projects found | | | |\n"
    
    return markdown, count

def main():
    args = parse_args()
    print("🚀 Starting precise Autonomi tracker...")
    repos = search_repositories(args)
    report, count = generate_report(repos, args)
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Found {count} relevant repositories")
    print("📄 Report saved to docs/index.md")

if __name__ == "__main__":
    main()
