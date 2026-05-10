import pytest
from custom_components.insane_updater.utils import parse_github_url

def test_parse_github_url_path_traversal():
    """Test that parse_github_url raises ValueError for path traversal."""
    with pytest.raises(ValueError, match="path traversal"):
        parse_github_url("../attacker/repo")

    with pytest.raises(ValueError, match="path traversal"):
        parse_github_url("owner/../attacker")

def test_parse_github_url_invalid_chars():
    """Test that parse_github_url raises ValueError for invalid characters."""
    with pytest.raises(ValueError, match="Invalid characters"):
        parse_github_url("owner!/repo")

    with pytest.raises(ValueError, match="Invalid characters"):
        parse_github_url("owner/repo$")

def test_parse_github_url_valid():
    """Test that valid URLs still work."""
    owner, repo = parse_github_url("https://github.com/babeinlovexd/insane_package_report")
    assert owner == "babeinlovexd"
    assert repo == "insane_package_report"

    owner, repo = parse_github_url("babeinlovexd/insane_package_report")
    assert owner == "babeinlovexd"
    assert repo == "insane_package_report"

    owner, repo = parse_github_url("owner/repo.name_with-chars")
    assert owner == "owner"
    assert repo == "repo.name_with-chars"
