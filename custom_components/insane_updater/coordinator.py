# https://github.com/babeinlovexd

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import COMMON_BRANCH_NAMES
from .utils import parse_github_url, GITHUB_NAME_RE

_LOGGER = logging.getLogger(__name__)

class GitHubPackageCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch GitHub package version info."""

    def __init__(self, hass: HomeAssistant, token: str, url: str, ref: str, pkg_type: str, update_interval: int) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Insane Updater {url}",
            update_interval=timedelta(hours=update_interval),
        )
        self.token = token
        self.url = url
        self.ref = ref
        self.pkg_type = pkg_type
        self.session = async_get_clientsession(hass)

        try:
            self.owner, self.repo = parse_github_url(self.url)
        except ValueError:
            self.owner, self.repo = None, None

        if self.ref and self.ref not in COMMON_BRANCH_NAMES:
            # ref can be a branch, tag or commit SHA.
            # Usually it's alphanumeric with some special chars.
            # We reuse GITHUB_NAME_RE but allow / for sub-branches like 'feature/something'
            if not all(GITHUB_NAME_RE.match(part) for part in self.ref.split("/") if part):
                _LOGGER.warning("Invalid characters in GitHub ref: %s", self.ref)
                self.ref = None
            elif ".." in self.ref:
                _LOGGER.warning("Path traversal attempt in GitHub ref: %s", self.ref)
                self.ref = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest version from GitHub."""

        if not self.owner or not self.repo:
            raise UpdateFailed(f"Invalid GitHub URL: {self.url}")

        owner, repo = self.owner, self.repo

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HomeAssistant-InsaneUpdater",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        api_url_base = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            if self.ref:
                is_branch = self.ref in COMMON_BRANCH_NAMES

                if not is_branch:
                    tags_url = f"{api_url_base}/tags"
                    async with self.session.get(tags_url, headers=headers) as resp:
                        resp.raise_for_status()
                        tags = await resp.json()

                        if tags and len(tags) > 0:
                            latest_tag = tags[0]
                            return {
                                "latest_version": latest_tag["name"],
                                "latest_commit": latest_tag["commit"]["sha"],
                                "release_url": f"https://github.com/{owner}/{repo}/releases/tag/{latest_tag['name']}"
                            }

                # Fallback to commits if it is a branch or no tags were found
                ref_url = f"{api_url_base}/commits/{self.ref}"
                async with self.session.get(ref_url, headers=headers) as ref_resp:
                    ref_resp.raise_for_status()
                    commit_data = await ref_resp.json()

                    version_str = f"{self.ref} ({commit_data['sha'][:7]})" if is_branch else self.ref

                    return {
                        "latest_version": version_str,
                        "latest_commit": commit_data["sha"],
                        "release_url": f"https://github.com/{owner}/{repo}/commits/{self.ref}"
                    }

            else:
                async with self.session.get(api_url_base, headers=headers) as resp:
                    resp.raise_for_status()
                    repo_info = await resp.json()
                    default_branch = repo_info.get("default_branch", "main")

                commits_url = f"{api_url_base}/commits/{default_branch}"
                async with self.session.get(commits_url, headers=headers) as resp:
                    resp.raise_for_status()
                    commit_data = await resp.json()

                    version_str = f"{default_branch} ({commit_data['sha'][:7]})"

                    return {
                        "latest_version": version_str,
                        "latest_commit": commit_data["sha"],
                        "release_url": f"https://github.com/{owner}/{repo}/commits/{default_branch}"
                    }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with GitHub API: {err}")
