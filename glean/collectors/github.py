"""GitHub public-profile collector. Uses the public REST API.

A GITHUB_TOKEN (read from the environment) raises rate limits but is optional.
Only public data is fetched.
"""

import logging

import requests

logger = logging.getLogger(__name__)

_API = "https://api.github.com"
_TIMEOUT = 10

TOOL = {
    "type": "function",
    "function": {
        "name": "github_profile",
        "description": (
            "Look up a public GitHub user or organization: profile metadata and "
            "their most recently updated public repositories. Useful for a "
            "person's or company's technical footprint."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "GitHub username or organization login.",
                }
            },
            "required": ["username"],
        },
    },
}


def _headers(github_token: str | None) -> dict[str, str]:
    """Build request headers, including auth only if a token is present."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "glean-osint"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def run(username: str, *, github_token: str | None = None) -> str:
    """Fetch a public GitHub profile and top repos. Returns text or an error."""
    handle = (username or "").strip().lstrip("@")
    if not handle:
        return "ERROR: empty username."

    headers = _headers(github_token)
    try:
        user_resp = requests.get(
            f"{_API}/users/{handle}", headers=headers, timeout=_TIMEOUT
        )
        if user_resp.status_code == 404:
            return f"No public GitHub account found for {handle!r}."
        user_resp.raise_for_status()
        user = user_resp.json()

        repos_resp = requests.get(
            f"{_API}/users/{handle}/repos",
            headers=headers,
            params={"sort": "updated", "per_page": 10},
            timeout=_TIMEOUT,
        )
        repos_resp.raise_for_status()
        repos = repos_resp.json()
    except requests.RequestException as exc:  # boundary: report to model
        logger.warning("github_profile failed for %r: %s", handle, exc)
        return f"ERROR: GitHub request failed: {exc}"

    profile = (
        f"GitHub: {user.get('login')} ({user.get('html_url')})\n"
        f"Name: {user.get('name')}\n"
        f"Company: {user.get('company')}\n"
        f"Location: {user.get('location')}\n"
        f"Bio: {user.get('bio')}\n"
        f"Public repos: {user.get('public_repos')}  Followers: {user.get('followers')}"
    )

    repo_lines = []
    for repo in repos:
        repo_lines.append(
            f"- {repo.get('name')} "
            f"({repo.get('language') or 'n/a'}, "
            f"{repo.get('stargazers_count', 0)} stars): "
            f"{(repo.get('description') or '').strip()} {repo.get('html_url')}"
        )

    repos_text = "\n".join(repo_lines) if repo_lines else "(no public repos)"
    return f"{profile}\n\nRecent public repositories:\n{repos_text}"
