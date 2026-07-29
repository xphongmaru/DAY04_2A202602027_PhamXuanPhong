from __future__ import annotations

import requests
from typing import Any
from tools._shared import TIMEOUT, err


def search_github(query: str = "", limit: int = 5, sort: str = "stars") -> dict[str, Any]:
    """Search public GitHub repositories for research code or libraries."""
    try:
        limit = max(1, min(int(limit or 5), 10))
        sort_choice = sort if sort in {"stars", "forks", "updated"} else "stars"
        
        url = "https://api.github.com/search/repositories"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "AI-Research-Agent/1.0"
        }
        params = {
            "q": query,
            "sort": sort_choice,
            "order": "desc",
            "per_page": limit
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        items: list[dict[str, Any]] = []
        for repo in data.get("items", []):
            items.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "language": repo.get("language"),
                "updated_at": repo.get("updated_at"),
                "source": "github.com"
            })
            
        return {
            "tool": "github",
            "query": query,
            "sort": sort_choice,
            "total_count": data.get("total_count", 0),
            "items": items
        }
    except Exception as exc:
        return err("github", exc)
