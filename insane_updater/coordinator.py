"""Data update coordinator for Insane Updater."""
import logging
from datetime import timedelta
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GITHUB_API_URL

_LOGGER = logging.getLogger(__name__)

class InsaneUpdaterCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from GitHub."""

    def __init__(self, hass: HomeAssistant, token: str | None) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.token = token
        self.repositories = {} # url -> details
        self.data = {} # url -> latest_version

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=24),
        )

    def add_repository(self, payload: dict) -> None:
        """Add a repository to check."""
        url = payload.get("url")
        if url and url not in self.repositories:
            self.repositories[url] = payload

    async def _async_update_data(self) -> dict:
        """Fetch data from GitHub API."""
        if not self.repositories:
            return {}

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HomeAssistant-InsaneUpdater"
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        results = {}

        session = async_get_clientsession(self.hass)

        for url, details in self.repositories.items():
            try:
                # url is in format "user/repo"
                ref = details.get("ref")

                # If no explicit ref is provided, we track the default branch's latest commit
                if not ref:
                    repo_api_url = f"{GITHUB_API_URL}/{url}"
                    async with session.get(repo_api_url, headers=headers) as repo_response:
                        if repo_response.status == 200:
                            repo_data = await repo_response.json()
                            ref = repo_data.get("default_branch", "main")
                        else:
                            ref = "main"

                    api_url = f"{GITHUB_API_URL}/{url}/commits/{ref}"
                    _LOGGER.debug("Fetching GitHub Branch API: %s", api_url)

                    async with session.get(api_url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and "sha" in data:
                                # We use the short SHA as the "version"
                                results[url] = data["sha"][:7]
                        elif response.status == 403 and "rate limit" in (await response.text()).lower():
                            _LOGGER.warning("GitHub API rate limit exceeded.")
                            break
                        else:
                            _LOGGER.warning("Failed to fetch branch %s: HTTP %s", url, response.status)

                else:
                    # A ref is provided. It's usually a tag or branch.
                    # If it's a tag, we should check for the *latest release* or latest tags instead
                    # of just polling the same static tag over and over.
                    # As a naive but effective strategy for packages: we check the default branch's
                    # latest commit anyway, and let the user see that the branch has moved ahead of their tag.
                    # Or, better: we query the `/tags` endpoint and get the newest tag if they are on a tag.
                    tags_url = f"{GITHUB_API_URL}/{url}/tags"
                    _LOGGER.debug("Fetching GitHub Tags API: %s", tags_url)

                    async with session.get(tags_url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and isinstance(data, list) and len(data) > 0:
                                # GitHub tags API returns tags in order, top is usually the newest
                                # We store the tag name (or short sha)
                                latest_tag = data[0].get("name")
                                latest_sha = data[0].get("commit", {}).get("sha", "")[:7]
                                # Store format: tag (sha) or just sha if we want to keep it simple
                                results[url] = f"{latest_tag} ({latest_sha})" if latest_tag else latest_sha
                            else:
                                # Fallback if no tags exist, just get the commit for their ref
                                api_url = f"{GITHUB_API_URL}/{url}/commits/{ref}"
                                async with session.get(api_url, headers=headers) as c_resp:
                                    if c_resp.status == 200:
                                        c_data = await c_resp.json()
                                        if c_data and "sha" in c_data:
                                            results[url] = c_data["sha"][:7]
                        elif response.status == 403 and "rate limit" in (await response.text()).lower():
                            _LOGGER.warning("GitHub API rate limit exceeded.")
                            break

                # Be nice to GitHub API limits
                await asyncio.sleep(1)

            except Exception as err:
                _LOGGER.error("Error updating %s: %s", url, err)

        return results
