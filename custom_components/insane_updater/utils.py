"""Utility functions for Insane Updater."""
from urllib.parse import urlparse

def parse_github_url(url: str) -> tuple[str, str]:
    """Parse GitHub URL to extract owner and repo.

    Args:
        url: The GitHub URL to parse.

    Returns:
        A tuple containing (owner, repo).

    Raises:
        ValueError: If the URL is invalid.
    """
    if not url:
        raise ValueError(f"Invalid GitHub URL: {url}")

    # Use urlparse to properly decompose the URL and handle query params/fragments
    parsed = urlparse(url)

    # If there's no scheme, urlparse might put the whole thing in path (e.g. owner/repo)
    # or if it starts with github.com/owner/repo
    path = parsed.path
    if not parsed.scheme and not parsed.netloc and not path.startswith("/"):
        # path is already set correctly
        pass
    elif parsed.netloc and parsed.netloc != "github.com":
        # If it's a full URL but not github.com, we still try to parse it
        # as the user might be using a proxy or enterprise instance
        pass

    parts = [p for p in path.split("/") if p]

    # Handle shorthand like github.com/owner/repo which urlparse puts in path
    if parts and parts[0] == "github.com":
        parts = parts[1:]

    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner = parts[0]
    repo = parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo
