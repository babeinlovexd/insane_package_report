import pytest
from components.insane_package_report import extract_github_info

@pytest.mark.parametrize(
    "data,item_type,expected",
    [
        # Dictionary style (packages)
        (
            {"pkg1": {"github": "owner/repo", "ref": "main"}},
            "packages",
            [{"url": "https://github.com/owner/repo", "ref": "main", "type": "packages"}]
        ),
        (
            {"pkg2": {"url": "https://github.com/owner/repo", "ref": "dev"}},
            "packages",
            [{"url": "https://github.com/owner/repo", "ref": "dev", "type": "packages"}]
        ),
        (
            {"pkg3": "github://owner/repo@v1.0.0"},
            "packages",
            [{"url": "https://github.com/owner/repo", "ref": "v1.0.0", "type": "packages"}]
        ),
        (
            {"pkg4": "github://owner/repo"},
            "packages",
            [{"url": "https://github.com/owner/repo", "ref": "", "type": "packages"}]
        ),
        (
            {"pkg5": {"github": "https://github.com/owner/repo"}},
            "packages",
            [{"url": "https://github.com/owner/repo", "ref": "", "type": "packages"}]
        ),
        # List style (external_components)
        (
            [{"source": {"type": "git", "url": "https://github.com/owner/repo", "ref": "main"}}],
            "external_components",
            [{"url": "https://github.com/owner/repo", "ref": "main", "type": "external_components"}]
        ),
        (
            [{"source": {"github": "owner/repo", "ref": "dev"}}],
            "external_components",
            [{"url": "https://github.com/owner/repo", "ref": "dev", "type": "external_components"}]
        ),
        (
            [{"source": "github://owner/repo@v2.0.0"}],
            "external_components",
            [{"url": "https://github.com/owner/repo", "ref": "v2.0.0", "type": "external_components"}]
        ),
        # Edge cases & Mixed
        ({}, "packages", []),
        ([], "external_components", []),
        (None, "packages", []),
        ({"pkg": {"other": "data"}}, "packages", []),
        ([{"other": "data"}], "external_components", []),
        ([{"source": {"type": "local", "path": "components"}}], "external_components", []),
        # Non-github git URLs should be ignored
        (
            [{"source": {"type": "git", "url": "https://gitlab.com/owner/repo"}}],
            "external_components",
            []
        ),
        # Already full github:// URL in dict
        (
            {"pkg": {"github": "github://owner/repo"}},
            "packages",
            [{"url": "github://owner/repo", "ref": "", "type": "packages"}]
        ),
    ],
)
def test_extract_github_info(data, item_type, expected):
    """Test extract_github_info with various inputs."""
    assert extract_github_info(data, item_type) == expected
