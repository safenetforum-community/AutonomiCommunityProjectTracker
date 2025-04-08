import requests
from datetime import datetime
import os
import re

# GitHub API setup
GITHUB_API_URL = "https://api.github.com/search/repositories"
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'} if TOKEN else {}

SEARCH_QUERIES = [
    'autonomi.com in:readme,description',
    '"Autonomi Network" in:readme,description',
    'autonomi.network in:readme,description',
    'autonomi in:readme,description -autonomous'
]

def search_github():
    all_repos = []
    for query in SEARCH_QUERIES:
        params = {
            'q': query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': 100
        }
        try:
            response = requests.get(GITHUB_API_URL, headers=HEADERS, params=params)
            response.raise_for_status()
            items = response.json().get('items', [])
            all_repos.extend(items)
            print(f"Found {len(items)} repos for: '{query}'")
        except Exception as e:
            print(f"Error searching '{query}': {str(e)[:100]}...")
    return all_repos

def is_autonomi_project(repo):
    """Verify genuine Autonomi references"""
    fields_to_check = [
        repo['name'],
        repo.get('description', ''),
        repo.get('homepage', ''),
        ' '.join(repo.get('topics', []))
    ]
    text = ' '.join(str(field) for field in fields_to_check).lower()
    
    patterns = [
        r'autonomi\.com',
        r'autonomi[\s-]network',
        r'autonomi/[\w-]+'  # Matches repo names like 'autonomi/sdk'
    ]
    return any(re.search(pattern, text, re.I) for pattern in patterns)

def generate_report(repos):
    markdown = """# Autonomi Community Project Tracker

| Repository | Description | Updated | Stars | Reference Type |
|------------|-------------|---------|-------|----------------|
"""
    for repo in sorted(repos, key=lambda x: x['updated_at'], reverse=True):
        ref_types = []
        if re.search(r'autonomi\.com', repo['html_url'], re.I):
            ref_types.append("URL")
        if re.search(r'autonomi network', repo.get('description', ''), re.I):
            ref_types.append("Name")
        if 'autonomi' in [t.lower() for t in repo.get('topics', [])]:
            ref_types.append("Topic")
        
        markdown += f"| [{repo['full_name']}]({repo['html_url']}) | {repo.get('description', '--')} | {repo['updated_at'][:10]} | {repo['stargazers_count']} | {', '.join(ref_types) or 'Content'} |\n"
    
    return markdown

def main():
    print("🚀 Starting Autonomi Community Project Tracker...")
    repos = search_github()
    filtered_repos = [r for r in repos if is_autonomi_project(r)]
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w') as f:
        f.write(generate_report(filtered_repos))
    
    print(f"✅ Found {len(filtered_repos)} Autonomi-related projects")
    print("📄 Report generated at docs/index.md")

if __name__ == "__main__":
    main()