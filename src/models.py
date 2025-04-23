from dataclasses import dataclass
from datetime import datetime

@dataclass
class Repository:
    name: str
    html_url: str
    description: str
    updated_at: datetime
    language: str
    stargazers_count: int