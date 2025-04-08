import requests
from datetime import datetime, timedelta
import os
import re
import time
import argparse
from collections import defaultdict

# GitHub API setup
GITHUB_API_URL = "https://api.github.com/search/repositories"
SEARCH_CODE_URL = "https://api.github.com/search/code"
TOKEN = os.getenv('GITHUB_TOKEN')
HEADERS = {'Authorization': f'token {TOKEN}'} if TOKEN else {}

# Configuration
REQUEST_DELAY = 2  # seconds between API calls
MAX_RETRIES = 2
SUPPRESS_ERRORS = True
MIN_START_DATE = "2024-01-01"  # Only projects created after this date

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--recent', action='store_true',
                       help='Only show projects updated in the last week')
    return parser.parse_args()

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
            print(f"⚠️ API error: {str(e)[:100]}...")
        return None

def build_search_query(base_query, args):
    """Build GitHub search query with date filters"""
    date_filters = []
    
    # Always filter by creation date
    date_filters.append(f"created:>{MIN_START_DATE}")
    
    # Add update filter if --recent flag is set
    if args.recent:
        last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_filters.append(f"updated:>{last_week}")
    
    return f"{base_query} {' '.join(date_filters)}"

def search_repositories(args):
    """Search GitHub for Autonomi-related repositories with date filters"""
    base_queries = [
        'autonomi.com in:name,description,readme',
        '"Autonomi Network" in:name,description,readme',
        'autonomi in:name,description,readme -autonomous'
    ]
    
    repos = []
    for base_query in base_queries:
        full_query = build_search_query(base_query, args)
        data = safe_request(GITHUB_API_URL, {
            'q': full_query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': 100
        })
        if data and 'items' in data:
            for item in data['items']:
                item['detected_terms'] = defaultdict(set)
                item['detected_terms']['Autonomi'].add(base_query.split()[0])
            repos.extend(data['items'])
            print(f"🔍 Found {len(data['items'])} repos for: '{full_query[:60]}...'")
    return repos

def generate_markdown_report(repositories, args):
    """Generate report with date filtering"""
    unique_repos = {}
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
            
        # Apply additional date filters if needed
        created_at = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        if created_at < datetime.strptime(MIN_START_DATE, '%Y-%m-%d'):
            continue
            
        if repo.get('html_url') in unique_repos:
            continue
            
        # Ensure all required fields exist
        repo.setdefault('full_name', 'Unknown')
        repo.setdefault('html_url', '#')
        repo.setdefault('description', '')
        repo.setdefault('updated_at', '1970-01-01')
        repo.setdefault('created_at', MIN_START_DATE)
        repo.setdefault('stargazers_count', 0)
        repo.setdefault('detected_terms', defaultdict(set))
        
        unique_repos[repo['html_url']] = repo
    
    # Prepare report header with filter info
    date_filters = f"Created after {MIN_START_DATE}"
    if args.recent:
        date_filters += " and updated in last week"
    
    markdown = f"""# Autonomi Community Project Tracker
### ({date_filters})

| Repository | Description | Created | Updated | Stars | References |
|------------|-------------|---------|---------|-------|------------|
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
        
        desc = (repo['description'] or '')[:100]
        desc += '...' if len(repo['description'] or '') > 100 else ''
        
        markdown += f"| [{repo['full_name']}]({repo['html_url']}) | {desc} | {repo['created_at'][:10]} | {repo['updated_at'][:10]} | {repo['stargazers_count']} | {', '.join(sorted(refs)) or 'Content'} |\n"
    
    return markdown

def main():
    args = parse_args()
    print("🚀 Starting Autonomi Community Project Tracker...")
    print(f"⏳ Filtering projects created after {MIN_START_DATE}")
    if args.recent:
        print("⏳ Only showing projects updated in the last week")
    
    repos = search_repositories(args)
    print(f"✅ Found {len(repos)} matching repositories")
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w', encoding='utf-8') as f:
        f.write(generate_markdown_report(repos, args))
    
    unique_count = len({r['html_url'] for r in repos if isinstance(r, dict)})
    print(f"📊 Found {unique_count} unique projects matching criteria")
    print("📄 Report saved to docs/index.md")

if __name__ == "__main__":
    main()
