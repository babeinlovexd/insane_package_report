import logging
from typing import Any

from homeassistant.core import HomeAssistant
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest version from GitHub."""

        # Parse github url to get owner/repo
        # https://github.com/owner/repo
        parts = self.url.rstrip('/').split('/')
        if len(parts) < 2:
            raise UpdateFailed(f"Invalid GitHub URL: {self.url}")

        owner = parts[-2]
        repo = parts[-1]

        if repo.endswith(".git"):
            repo = repo[:-4]

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HomeAssistant-InsaneUpdater",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        api_url_base = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            if self.ref:
                # We have a specific ref (could be a branch, tag, or commit).
                # The user wants to know if there is a NEWER tag than the current ref.
                # But wait, if self.ref is "main" or "master", and the repo HAS tags,
                # we don't want to show a tag as an update for a branch track!
                # Let's check if the ref is a known branch name.
                is_branch = self.ref in ["main", "master", "dev", "develop"]

                tags_url = f"{api_url_base}/tags"
                async with self.session.get(tags_url, headers=headers) as resp:
                    resp.raise_for_status()
                    tags = await resp.json()

                    # If the ref is just a branch name, or there are no tags,
                    # we should track the branch commit, not the latest tag.
                    # Or if they provided a commit hash, it might not be a tag.
                    # But the simplest is: if they explicitly track main/master, they don't want tags.

                    if tags and len(tags) > 0 and not is_branch:
                        latest_tag = tags[0]
                        return {
                            "latest_version": latest_tag["name"],
                            "latest_commit": latest_tag["commit"]["sha"],
                            "release_url": f"https://github.com/{owner}/{repo}/releases/tag/{latest_tag['name']}"
                        }
                    else:
                        # Fallback if no tags but ref is provided, or ref is a branch, just get the ref commit
                        ref_url = f"{api_url_base}/commits/{self.ref}"
                        async with self.session.get(ref_url, headers=headers) as ref_resp:
                            ref_resp.raise_for_status()
                            commit_data = await ref_resp.json()
                            return {
                                "latest_version": self.ref,
                                "latest_commit": commit_data["sha"],
                                "release_url": f"https://github.com/{owner}/{repo}/commits/{self.ref}"
                            }

            else:
                # No ref provided. Find default branch, then get latest commit.
                async with self.session.get(api_url_base, headers=headers) as resp:
                    resp.raise_for_status()
                    repo_info = await resp.json()
                    default_branch = repo_info.get("default_branch", "main")

                commits_url = f"{api_url_base}/commits/{default_branch}"
                async with self.session.get(commits_url, headers=headers) as resp:
                    resp.raise_for_status()
                    commit_data = await resp.json()

                    return {
                        "latest_version": default_branch,
                        "latest_commit": commit_data["sha"],
                        "release_url": f"https://github.com/{owner}/{repo}/commits/{default_branch}"
                    }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with GitHub API: {err}")
