"""Data update coordinator for Safe Swim."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SafeSwimAPI, SafeSwimAPIError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SafeSwimCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Safe Swim data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: SafeSwimAPI,
        location_slug: str,
        location_name: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.location_slug = location_slug
        self.location_name = location_name

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{location_slug}",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Safe Swim API.
        
        Returns:
            Dictionary containing location and forecast data.
            
        Raises:
            UpdateFailed: If unable to fetch data.
        """
        try:
            data = await self.api.get_location_forecast(self.location_slug)
            
            if data is None:
                raise UpdateFailed(
                    f"Location {self.location_slug} not found"
                )
            
            # Structure the data for easy access by sensors
            structured_data = {
                "location": {
                    "id": data.get("id"),
                    "name": data.get("name", self.location_name),
                    "alternative_name": data.get("alternative_name"),
                    "description": data.get("description"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "patrolled": data.get("patrolled", False),
                    "tags": data.get("tags", []),
                    "cam_id": data.get("camId"),
                },
                "forecasts": data.get("forecasts", {}),
                "alerts": data.get("alerts", []),
                "patrols": data.get("patrols", []),
            }
            
            _LOGGER.debug(
                "Successfully fetched data for %s: %d forecast types",
                self.location_slug,
                len(structured_data["forecasts"]),
            )
            
            return structured_data
            
        except SafeSwimAPIError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
