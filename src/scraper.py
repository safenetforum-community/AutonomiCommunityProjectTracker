from github import Github
import os
from datetime import datetime
from dotenv import load_dotenv
from .models import Repository

load_dotenv()

def search_repos(max_results=100):
    """Search GitHub for Autonomi repos with network/nodes keywords"""
    g = Github(os.getenv('GITHUB_TOKEN'))
    
    query = 'Autonomi+(network|nodes)+in:name,description'
    results = g.search_repositories(query, sort='updated', order='desc')
    
    repos = []
    for repo in results:
        repos.append(Repository(
            name=repo.name,
            html_url=repo.html_url,
            description=repo.description,
            updated_at=repo.updated_at,
            language=repo.language,
            stargazers_count=repo.stargazers_count
        ))
        if len(repos) >= max_results:
            break
    
    repos = filter_by_date(repos)
    return filter_by_language(repos)

def filter_by_date(repos, min_date=datetime(2024, 1, 1)):
    """Filter repos updated since min_date"""
    return [repo for repo in repos if repo.updated_at >= min_date]

def filter_by_language(repos):
    """Exclude Italian-only repositories"""
    return [repo for repo in repos 
            if not repo.language or repo.language.lower() != 'italian']