"""Minimal read-only Reddit Data API connector for SC Scout.

This public review version intentionally contains no SC Scout detector logic,
OpenAI integration, private data, or API credentials.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE = "https://oauth.reddit.com"


@dataclass
class RedditPost:
    source: str
    source_type: str
    community: str
    source_native_id: str
    title: str
    text: str
    published_at: str
    url: str
    content_type: str
    engagement: dict[str, int | None]


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_access_token(session: requests.Session | None = None) -> str:
    """Request an application-only OAuth token using installed credentials."""
    client_id = _required_env("SCOUT_REDDIT_CLIENT_ID")
    client_secret = _required_env("SCOUT_REDDIT_CLIENT_SECRET")
    user_agent = _required_env("SCOUT_REDDIT_USER_AGENT")

    http = session or requests.Session()
    response = http.post(
        TOKEN_URL,
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": user_agent},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Reddit OAuth response did not include access_token")
    return token


def fetch_new_posts(
    communities: Iterable[str],
    *,
    limit: int = 100,
    session: requests.Session | None = None,
) -> list[RedditPost]:
    """Fetch newest public posts from selected public subreddits.

    The connector is read-only. It does not post, comment, vote, message users,
    moderate communities, or access private Reddit data.
    """
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    token = get_access_token(session=session)
    user_agent = _required_env("SCOUT_REDDIT_USER_AGENT")
    http = session or requests.Session()
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": user_agent,
    }

    results: list[RedditPost] = []

    for community in communities:
        subreddit = community.strip().removeprefix("r/")
        if not subreddit:
            continue

        response = http.get(
            f"{API_BASE}/r/{subreddit}/new",
            params={"limit": limit},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        for child in payload.get("data", {}).get("children", []):
            post = child.get("data", {})
            created_utc = post.get("created_utc")
            published_at = (
                datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
                if created_utc is not None
                else None
            )

            permalink = post.get("permalink") or ""
            url = f"https://www.reddit.com{permalink}" if permalink else post.get("url") or ""

            results.append(
                RedditPost(
                    source="Reddit",
                    source_type="forum",
                    community=f"r/{post.get('subreddit') or subreddit}",
                    source_native_id=post.get("name") or post.get("id") or "",
                    title=post.get("title") or "",
                    text=post.get("selftext") or "",
                    published_at=published_at or "",
                    url=url,
                    content_type="post",
                    engagement={
                        "comments": post.get("num_comments"),
                        "score": post.get("score"),
                        "views": None,
                        "reactions": None,
                    },
                )
            )

        # Polite pacing between communities. Reddit's own rate-limit headers
        # should be respected in production; this small delay is an additional
        # conservative safeguard for the prototype.
        time.sleep(0.5)

    return results


def load_communities(config_path: str | Path) -> list[str]:
    payload = json.loads(Path(config_path).read_text(encoding="utf-8"))
    communities = payload.get("communities")
    if not isinstance(communities, list) or not all(isinstance(x, str) for x in communities):
        raise ValueError("Config must contain a string list named 'communities'")
    return communities


def write_jsonl(posts: Iterable[RedditPost], output_path: str | Path) -> None:
    path = Path(output_path)
    with path.open("w", encoding="utf-8") as handle:
        for post in posts:
            handle.write(json.dumps(asdict(post), ensure_ascii=False) + "\n")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Read-only Reddit connector for SC Scout")
    parser.add_argument("--config", default="example_config.json")
    parser.add_argument("--output", default="reddit_posts.jsonl")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    communities = load_communities(args.config)
    posts = fetch_new_posts(communities, limit=args.limit)
    write_jsonl(posts, args.output)
    print(f"Collected {len(posts)} public Reddit posts")


if __name__ == "__main__":
    main()
