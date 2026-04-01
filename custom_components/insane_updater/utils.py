"""Utility functions for Insane Updater."""

def parse_github_url(url: str) -> tuple[str, str]:
    """Parse GitHub URL to extract owner and repo.

    Args:
        url: The GitHub URL to parse.

    Returns:
        A tuple containing (owner, repo).

    Raises:
        ValueError: If the URL is invalid.
    """
    parts = url.rstrip("/").split("/")

    # If it is a full URL, owner and repo are at the end
    if len(parts) >= 3 and parts[0].startswith("http"):
        # We expect at least something like https://github.com/owner/repo (5 parts)
        if len(parts) < 5:
            raise ValueError(f"Invalid GitHub URL: {url}")
    elif len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner = parts[-2]
    repo = parts[-1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo
