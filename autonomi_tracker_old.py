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

# Rate limiting and error handling
REQUEST_DELAY = 2  # seconds between API calls
MAX_RETRIES = 2
SUPPRESS_CODE_SEARCH_ERRORS = True  # Set to False to see code search errors

def make_github_request(url, params=None, retry_count=0):
    """Safe GitHub API request with error handling"""
    time.sleep(REQUEST_DELAY)
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if retry_count < MAX_RETRIES:
            time.sleep(5)  # Longer delay before retry
            return make_github_request(url, params, retry_count + 1)
        if not (SUPPRESS_CODE_SEARCH_ERRORS and 'search/code' in url):
            print(f"⚠️ API request failed for {url.split('?')[0]}: {str(e)[:100]}...")
        return None
    except requests.exceptions.RequestException as e:
        if not (SUPPRESS_CODE_SEARCH_ERRORS and 'search/code' in url):
            print(f"⚠️ API request failed for {url.split('?')[0]}: {str(e)[:100]}...")
        return None

def search_github_repos():
    """Search repository metadata"""
    all_repos = []
    queries = [
        'autonomi.com in:name,description,readme',
        '"Autonomi Network" in:name,description,readme',
        'autonomi in:name,description,readme -autonomous'
    ]
    
    for query in queries:
        params = {
            'q': query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': 100
        }
        data = make_github_request(GITHUB_API_URL, params)
        if data and 'items' in data:
            for item in data['items']:
                if 'detected_terms' not in item:
                    item['detected_terms'] = defaultdict(set)
                item['detected_terms']['Autonomi'].add(query.split()[0])
            all_repos.extend(data['items'])
            print(f"🔍 Found {len(data['items'])} repos for: '{query[:50]}...'")
    return all_repos

def search_repo_content(repo):
    """Search repository content (READMEs, code) with error suppression"""
    findings = defaultdict(set)
    
    # Skip content search for very large repos to avoid timeouts
    if repo.get('size', 0) > 50000:  # Repo size in KB
        return findings
    
    # Search README files
    readme_params = {
        'q': f'repo:{repo["full_name"]} filename:README.md',
        'per_page': 1
    }
    readme_data = make_github_request(SEARCH_CODE_URL, readme_params)
    
    if readme_data and 'items' in readme_data and readme_data['items']:
        readme_url = readme_data['items'][0]['git_url']
        readme_content = make_github_request(readme_url)
        if readme_content and 'content' in readme_content:
            content = readme_content['content']
            if 'autonomi.com' in content.lower():
                findings['Autonomi'].add('autonomi.com')
            if 'autonomi network' in content.lower():
                findings['Autonomi'].add('network')
    
    return findings

def generate_report(repos):
    """Generate Markdown report with unique repositories"""
    unique_repos = {}
    for repo in repos:
        if repo['html_url'] not in unique_repos:
            unique_repos[repo['html_url']] = repo
    
    markdown = """# Autonomi Community Project Tracker

| Repository | Description | Updated | Stars | References |
|------------|-------------|---------|-------|------------|
"""
    for repo in sorted(unique_repos.values(), 
                     key=lambda x: x['updated_at'], 
                     reverse=True):
        refs = set()
        if 'autonomi.com' in repo['html_url'].lower():
            refs.add('URL')
        if 'autonomi' in (repo.get('description') or '').lower():
            refs.add('Description')
        if 'autonomi' in [t.lower() for t in repo.get('topics', [])]:
            refs.add('Topic')
        
        # Add content findings
        for ref_type in repo.get('detected_terms', {}).get('Autonomi', []):
            refs.add(ref_type)
        
        refs_str = ', '.join(sorted(refs)) if refs else 'Content'
        
        markdown += f"| [{repo['full_name']}]({repo['html_url']}) | {repo.get('description', '')[:100]}{'...' if len(repo.get('description', '')) > 100 else ''} | {repo['updated_at'][:10]} | {repo['stargazers_count']} | {refs_str} |\n"
    
    return markdown

def main():
    print("🚀 Starting Autonomi Community Project Tracker...")
    print("⏳ This may take a few minutes...")
    
    repos = search_github_repos()
    print(f"✅ Found {len(repos)} potential Autonomi-related repositories")
    
    # Skip content search if token not provided
    if not TOKEN:
        print("⚠️ No GitHub token provided - skipping deep content search")
    else:
        print("🔍 Searching repository content (READMEs, etc.)...")
        for i, repo in enumerate(repos):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(repos)} repositories...")
            findings = search_repo_content(repo)
            if findings:
                repo['detected_terms']['Autonomi'].update(findings['Autonomi'])
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/index.md', 'w') as f:
        f.write(generate_report(repos))
    
    unique_count = len(set(r['html_url'] for r in repos))
    print(f"📊 Found {unique_count} unique Autonomi-related projects")
    print("📄 Report generated at docs/index.md")

if __name__ == "__main__":
    main()
