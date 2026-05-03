import pytest
from custom_components.insane_updater.utils import parse_github_url

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo/", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("http://github.com/owner/repo", ("owner", "repo")),
        ("github.com/owner/repo", ("owner", "repo")),
        ("owner/repo", ("owner", "repo")),
        ("owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo?query=1", ("owner", "repo")),
        ("https://github.com/owner/repo#fragment", ("owner", "repo")),
        ("https://github.com/owner/repo/tree/main", ("owner", "repo")),
        ("https://github.com/owner/repo.git?foo=bar", ("owner", "repo")),
    ],
)
def test_parse_github_url_valid(url, expected):
    """Test parse_github_url with valid URLs."""
    assert parse_github_url(url) == expected

@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/owner",
        "https://github.com/",
        "repo",
        "",
        "/",
    ],
)
def test_parse_github_url_invalid(url):
    """Test parse_github_url with invalid URLs."""
    with pytest.raises(ValueError, match="Invalid GitHub URL"):
        parse_github_url(url)
