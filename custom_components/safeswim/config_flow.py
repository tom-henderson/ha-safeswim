"""Config flow for Safe Swim integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SafeSwimAPI, SafeSwimAPIError
from .const import CONF_LOCATION_NAME, CONF_LOCATION_SLUG, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_location(hass: HomeAssistant, slug: str) -> dict[str, str]:
    """Validate the location exists and return location data.
    
    Args:
        hass: Home Assistant instance
        slug: Location slug to validate
        
    Returns:
        Dictionary with location name
        
    Raises:
        SafeSwimAPIError: If API request fails
        ValueError: If location not found
    """
    session = async_get_clientsession(hass)
    api = SafeSwimAPI(session)
    
    data = await api.get_location_forecast(slug)
    if data is None:
        raise ValueError("Location not found")
    
    return {"name": data.get("name", slug)}


class SafeSwimConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Safe Swim."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._locations: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Fetch locations on first display
        if not self._locations:
            try:
                session = async_get_clientsession(self.hass)
                api = SafeSwimAPI(session)
                self._locations = await api.get_locations()
                
                if not self._locations:
                    errors["base"] = "no_locations"
                    return self.async_show_form(
                        step_id="user",
                        errors=errors,
                    )
                    
            except SafeSwimAPIError:
                _LOGGER.exception("Error fetching locations")
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="user",
                    errors=errors,
                )

        if user_input is not None:
            slug = user_input[CONF_LOCATION_SLUG]
            
            # Set unique ID to prevent duplicate config entries
            await self.async_set_unique_id(slug)
            self._abort_if_unique_id_configured()

            try:
                # Validate the location
                location_data = await validate_location(self.hass, slug)
                
                # Create the config entry
                return self.async_create_entry(
                    title=location_data["name"],
                    data={
                        CONF_LOCATION_SLUG: slug,
                        CONF_LOCATION_NAME: location_data["name"],
                    },
                )
            except ValueError:
                errors["base"] = "location_not_found"
            except SafeSwimAPIError:
                _LOGGER.exception("Error validating location")
                errors["base"] = "cannot_connect"

        # Create location options sorted by name
        location_options = {
            loc["slug"]: loc["name"]
            for loc in sorted(self._locations, key=lambda x: x["name"])
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION_SLUG): vol.In(location_options),
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        
        # Get the config entry being reconfigured
        entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        
        if entry is None:
            return self.async_abort(reason="reconfigure_failed")

        # Fetch locations if not already loaded
        if not self._locations:
            try:
                session = async_get_clientsession(self.hass)
                api = SafeSwimAPI(session)
                self._locations = await api.get_locations()
                
                if not self._locations:
                    errors["base"] = "no_locations"
                    return self.async_show_form(
                        step_id="reconfigure",
                        errors=errors,
                    )
                    
            except SafeSwimAPIError:
                _LOGGER.exception("Error fetching locations")
                errors["base"] = "cannot_connect"
                return self.async_show_form(
                    step_id="reconfigure",
                    errors=errors,
                )

        if user_input is not None:
            slug = user_input[CONF_LOCATION_SLUG]

            try:
                # Validate the location
                location_data = await validate_location(self.hass, slug)
                
                # Update the config entry
                return self.async_update_reload_and_abort(
                    entry,
                    title=location_data["name"],
                    data={
                        CONF_LOCATION_SLUG: slug,
                        CONF_LOCATION_NAME: location_data["name"],
                    },
                )
            except ValueError:
                errors["base"] = "location_not_found"
            except SafeSwimAPIError:
                _LOGGER.exception("Error validating location")
                errors["base"] = "cannot_connect"

        # Create location options sorted by name
        location_options = {
            loc["slug"]: loc["name"]
            for loc in sorted(self._locations, key=lambda x: x["name"])
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LOCATION_SLUG,
                        default=entry.data.get(CONF_LOCATION_SLUG),
                    ): vol.In(location_options),
                }
            ),
            errors=errors,
        )
