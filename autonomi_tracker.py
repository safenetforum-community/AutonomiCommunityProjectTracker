import requests
from datetime import datetime
import os
import re
import time
from collections import defaultdict

# GitHub API setup
GITHUB_API_URL = "https://api.github.com/search/repositories"
SEARCH_CODE_URL = "https://api.github.com/search/code"
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'} if TOKEN else {}

# Configuration
REQUEST_DELAY = 2  # seconds between API calls
MAX_RETRIES = 2
SUPPRESS_ERRORS = True  # Set to False for debugging

def safe_request(url, params=None, retry=0):
    """Robust API request handler with error suppression"""
    time.sleep(REQUEST_DELAY)
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if retry < MAX_RETRIES:
            time.sleep(5)
            return safe_request(url, params, retry + 1)
        if not SUPPRESS_ERRORS:
            print(f"⚠️ API error ({response.status_code if 'response' in locals() else 'N/A'}): {str(e)[:100]}...")
        return None

def search_repositories():
    """Search GitHub for Autonomi-related repositories"""
    queries = [
        'autonomi.com in:name,description,readme',
        '"Autonomi Network" in:name,description,readme',
        'autonomi in:name,description,readme -autonomous'
    ]
    
    repos = []
    for query in queries:
        data = safe_request(GITHUB_API_URL, {
            'q': query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': 100
        })
        if data and 'items' in data:
            for item in data['items']:
                item['detected_terms'] = defaultdict(set)
                item['detected_terms']['Autonomi'].add(query.split()[0])
            repos.extend(data['items'])
            print(f"🔍 Found {len(data['items'])} repos for: '{query[:50]}...'")
    return repos

def scan_repo_content(repo):
    """Safely scan repository content for references"""
    if repo.get('size', 0) > 50000:  # Skip large repos
        return {}
    
    findings = defaultdict(set)
    
    # Search README
    readme_data = safe_request(SEARCH_CODE_URL, {
        'q': f'repo:{repo["full_name"]} filename:README.md',
        'per_page': 1
    })
    
    if readme_data and 'items' in readme_data and readme_data['items']:
        content = safe_request(readme_data['items'][0]['git_url'])
        if content and 'content' in content:
            text = content['content'].lower()
            if 'autonomi.com' in text:
                findings['Autonomi'].add('autonomi.com')
            if 'autonomi network' in text:
                findings['Autonomi'].add('network')
    
    return findings

def generate_markdown_report(repositories):
    """Generate report with robust null checking"""
    unique_repos = {}
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
        if repo.get('html_url') in unique_repos:
            continue
            
        # Ensure all required fields exist
        repo.setdefault('full_name', 'Unknown')
        repo.setdefault('html_url', '#')
        repo.setdefault('description', '')
        repo.setdefault('updated_at', '1970-01-01')
        repo.setdefault('stargazers_count', 0)
        repo.setdefault('detected_terms', defaultdict(set))
        
        unique_repos[repo['html_url']] = repo
    
    markdown = """# Autonomi Community Project Tracker

| Repository | Description | Updated | Stars | References |
|------------|-------------|---------|-------|------------|
"""
    for repo in sorted(unique_repos.values(), key=lambda x: x['updated_at'], reverse=True):
        # Safely build references string
        refs = set()
        if 'autonomi.com' in (repo.get('html_url') or '').lower():
            refs.add('URL')
        if 'autonomi' in (repo.get('description') or '').lower():
            refs.add('Description')
        if 'autonomi' in [t.lower() for t in repo.get('topics', [])]:
            refs.add('Topic')
        
        # Add content findings
        for term in repo['detected_terms'].get('Autonomi', []):
            refs.add(term.split('.')[0])  # Remove domain if present
        
        desc = (repo['description'] or '')[:100]
        desc += '...' if len(repo['description'] or '') > 100 else ''
        
        markdown += f"| [{repo['full_name']}]({repo['html_url']}) | {desc} | {repo['updated_at'][:10]} | {repo['stargazers_count']} | {', '.join(sorted(refs)) or 'Content'} |\n"
    
    return markdown

def main():
    print("🚀 Starting Autonomi Community Project Tracker...")
    print("⏳ This may take a few minutes...")
    
    repos = search_repositories()
    print(f"✅ Found {len(repos)} potential repositories")
    
    if TOKEN:
        print("🔍 Scanning repository content...")
        for i, repo in enumerate(repos):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(repos)} repositories...")
            findings = scan_repo_content(repo)
            if findings:
                repo['detected_terms']['Autonomi'].update(findings['Autonomi'])
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w', encoding='utf-8') as f:
        f.write(generate_markdown_report(repos))
    
    unique_count = len({r['html_url'] for r in repos if isinstance(r, dict)})
    print(f"📊 Found {unique_count} unique Autonomi projects")
    print("📄 Report saved to docs/index.md")

if __name__ == "__main__":
    main()
