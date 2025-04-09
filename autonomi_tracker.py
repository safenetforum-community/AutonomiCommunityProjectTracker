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
MAX_RETRIES = 3
SUPPRESS_ERRORS = False  # Set to True after debugging
MIN_START_DATE = "2024-01-01"
TRACKER_REPO = "AutonomiCommunityProjectTracker"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Track Autonomi-related GitHub projects')
    parser.add_argument('--recent', action='store_true',
                      help='Only show projects updated in the last week')
    parser.add_argument('--debug', action='store_true',
                      help='Show debug information')
    return parser.parse_args()

def safe_request(url, params=None, retry=0):
    """Robust API request handler with error suppression"""
    time.sleep(REQUEST_DELAY)
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if args.debug:
            print(f"DEBUG: Request to {url.split('?')[0]} - Status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG: Response: {response.text[:200]}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if retry < MAX_RETRIES:
            time.sleep(5 * (retry + 1))
            return safe_request(url, params, retry + 1)
        if not SUPPRESS_ERRORS:
            print(f"⚠️ API error ({response.status_code if 'response' in locals() else 'N/A'}): {str(e)[:100]}...")
        return None

def build_search_queries(args):
    """Generate comprehensive search queries"""
    search_terms = [
        'autonomi.com',
        'autonomi network',
        'autonomi',
        'ant network',
        'autonomi/ant',
        'safe network',
        'maidsafe',
        'autonomous internet',
        'decentralized storage'
    ]
    
    search_fields = ['name', 'description', 'readme', 'topics']
    queries = []
    
    for term in search_terms:
        for field in search_fields:
            query = f'{term} in:{field}'
            if args.recent:
                last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                query += f' created:>{MIN_START_DATE} updated:>{last_week}'
            else:
                query += f' created:>{MIN_START_DATE}'
            queries.append(query)
    
    # Always include the tracker itself
    queries.append(f'{TRACKER_REPO} in:name')
    return queries

def search_repositories(args):
    """Search GitHub for Autonomi-related repositories"""
    queries = build_search_queries(args)
    repos = []
    
    for query in queries:
        if args.debug:
            print(f"DEBUG: Executing query: {query[:80]}...")
        
        data = safe_request(GITHUB_API_URL, {
            'q': query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': 100
        })
        
        if data and 'items' in data:
            if args.debug:
                print(f"DEBUG: Found {len(data['items'])} results for query")
            
            for item in data['items']:
                if 'detected_terms' not in item:
                    item['detected_terms'] = defaultdict(set)
                item['detected_terms']['Autonomi'].add(query.split()[0])
            repos.extend(data['items'])
    
    return repos

def generate_daily_report(repositories, args):
    """Generate daily report with all projects"""
    unique_repos = {}
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
            
        # Always include the tracker project
        if TRACKER_REPO.lower() in repo.get('full_name', '').lower():
            unique_repos[repo['html_url']] = repo
            continue
            
        # Apply date filters to other projects
        try:
            created_at = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            if created_at < datetime.strptime(MIN_START_DATE, '%Y-%m-%d'):
                continue
        except:
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
    
    date_filters = f"Created after {MIN_START_DATE}"
    if args.recent:
        date_filters += " and updated in last week"
    
    markdown = f"""# Autonomi Community Project Tracker
### ({date_filters})

| Repository | Description | Created | Updated | Stars | References |
|------------|-------------|---------|---------|-------|------------|
"""
    for repo in sorted(unique_repos.values(), key=lambda x: x['updated_at'], reverse=True):
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

def generate_weekly_report(repositories):
    """Generate weekly report of recently updated projects"""
    one_week_ago = datetime.now() - timedelta(days=7)
    
    weekly_repos = []
    for repo in repositories:
        if not isinstance(repo, dict):
            continue
            
        try:
            updated_at = datetime.strptime(repo.get('updated_at', ''), '%Y-%m-%dT%H:%M:%SZ')
            created_at = datetime.strptime(repo.get('created_at', ''), '%Y-%m-%dT%H:%M:%SZ')
            
            # Always include the tracker project
            if TRACKER_REPO.lower() in repo.get('full_name', '').lower():
                weekly_repos.append(repo)
                continue
                
            if updated_at >= one_week_ago:
                weekly_repos.append(repo)
        except:
            continue
    
    markdown = """# Autonomi Weekly Update Report
### (Projects updated in the last 7 days)

| Repository | Description | Updated | Stars | Changes |
|------------|-------------|---------|-------|---------|
"""
    for repo in sorted(weekly_repos, key=lambda x: x['updated_at'], reverse=True):
        created_at = datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        changes = "New project" if created_at >= one_week_ago else "Updated"
        
        markdown += f"""| [{repo['full_name']}]({repo['html_url']}) | {repo.get('description', '')[:100]}... | {repo['updated_at'][:10]} | {repo['stargazers_count']} | {changes} |
"""
    return markdown, len(weekly_repos)

def main():
    global args
    args = parse_args()
    print("🚀 Starting Autonomi Community Project Tracker...")
    print(f"⏳ Filtering projects created after {MIN_START_DATE}")
    if args.recent:
        print("⏳ Only showing projects updated in the last week")
    
    repos = search_repositories(args)
    print(f"✅ Found {len(repos)} matching repositories")
    
    if args.debug:
        print("\nDEBUG: Sample repositories found:")
        for repo in repos[:min(5, len(repos))]:
            print(f"- {repo['full_name']} (Updated: {repo['updated_at']}, Created: {repo['created_at']})")
    
    # Generate both reports
    daily_report = generate_daily_report(repos, args)
    weekly_report, weekly_count = generate_weekly_report(repos)
    
    # Save both files
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w', encoding='utf-8') as f:
        f.write(daily_report)
    with open('docs/weekly.md', 'w', encoding='utf-8') as f:
        f.write(weekly_report)
    
    print(f"📊 Weekly report: {weekly_count} updated projects")
    print("📄 Reports saved to docs/index.md and docs/weekly.md")

if __name__ == "__main__":
    main()