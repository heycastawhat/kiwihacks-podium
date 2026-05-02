"""
GitHub repository validator.

Instant check: regex match on the URL shape (used frontend-side too).
Background check: calls the public GitHub REST API to verify the repo exists
and is accessible. No auth token required for public repos — rate limit is
60 req/hr per IP, which is fine for background validation.
"""

import re
from urllib.parse import urlparse

import httpx

from podium.validators.base import ValidationResult

GITHUB_URL_PATTERN = re.compile(
    r"^(https?://)?github\.com/(?P<owner>[a-zA-Z0-9\-_]+)/(?P<repo>[a-zA-Z0-9\-_.]+)",
    re.IGNORECASE,
)

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}"


def _parse_url(url: str):
    value = (url or "").strip()
    if not value:
        return urlparse("")
    if "://" not in value:
        value = f"https://{value}"
    return urlparse(value)


def _parse_owner_repo(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub URL, or None if not parseable."""
    m = GITHUB_URL_PATTERN.match(url)
    if not m:
        return None
    return m.group("owner"), m.group("repo")


def is_github_url(url: str) -> bool:
    """Return True if the URL matches the GitHub repo format."""
    return bool(GITHUB_URL_PATTERN.match(url))


def is_git_url(url: str) -> bool:
    """Return True for GitHub, GitLab, or another repo URL on a git domain."""
    parsed = _parse_url(url)
    host = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]
    return "git" in host and len(path_parts) >= 2


async def validate_git_url(repo_url: str) -> ValidationResult:
    """
    Check whether a URL looks like a repo on a git-hosted domain.

    This validates shape only. Self-hosted GitLab/Gitea/Git web hosts often need
    auth or custom API paths, so existence checks stay GitHub-specific.
    """
    if is_git_url(repo_url):
        return ValidationResult(valid=True, message="")
    return ValidationResult(
        valid=False,
        message="Repository URL must use a git host (e.g. github.com/owner/repo, gitlab.com/owner/repo, or another domain containing 'git').",
    )


async def validate(repo_url: str, timeout: float = 10.0) -> ValidationResult:
    """
    Check whether a GitHub repository exists and is publicly accessible.

    Returns a warning if the repo is not found (404) or returns an error,
    since it may simply be a private repo the API can't see.
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return ValidationResult(
            valid=False,
            message="Repository URL must be a GitHub URL (e.g. github.com/owner/repo).",
        )

    owner, repo = parsed
    # Strip .git suffix if present
    repo = repo.removesuffix(".git")

    api_url = GITHUB_API.format(owner=owner, repo=repo)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        ) as client:
            response = await client.get(api_url)

        if response.status_code == 200:
            return ValidationResult(valid=True, message="")
        if response.status_code == 404:
            return ValidationResult(
                valid=False,
                message=f"Repository {owner}/{repo} was not found on GitHub. Make sure it is public.",
            )
        # Any other status (rate limit, server error) — soft warning rather than hard fail
        return ValidationResult(
            valid=False,
            message=f"Could not verify repository {owner}/{repo} (GitHub returned {response.status_code}).",
        )
    except Exception:
        return ValidationResult(
            valid=False,
            message=f"Could not reach GitHub to verify repository {owner}/{repo}.",
        )
