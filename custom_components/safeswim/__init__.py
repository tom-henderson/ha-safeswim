"""The Safe Swim integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SafeSwimAPI
from .const import CONF_LOCATION_NAME, CONF_LOCATION_SLUG, DOMAIN
from .coordinator import SafeSwimCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Safe Swim from a config entry."""
    location_slug = entry.data[CONF_LOCATION_SLUG]
    location_name = entry.data[CONF_LOCATION_NAME]

    # Create API client
    session = async_get_clientsession(hass)
    api = SafeSwimAPI(session)

    # Create coordinator
    coordinator = SafeSwimCoordinator(
        hass,
        api,
        location_slug,
        location_name,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Safe Swim integration set up for %s", location_name)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)

        _LOGGER.info("Safe Swim integration unloaded for %s", entry.data[CONF_LOCATION_NAME])

    return unload_ok
