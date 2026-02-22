"""API client for Safe Swim."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class SafeSwimAPIError(Exception):
    """Base exception for Safe Swim API errors."""


class SafeSwimAPIConnectionError(SafeSwimAPIError):
    """Exception for connection errors."""


class SafeSwimAPI:
    """API client for Safe Swim."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session

    async def get_locations(self) -> list[dict[str, Any]]:
        """Fetch all available locations.
        
        Returns:
            List of location dictionaries with name, slug, position, etc.
            
        Raises:
            SafeSwimAPIConnectionError: If unable to connect to API.
            SafeSwimAPIError: For other API errors.
        """
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with self._session.get(
                    f"{API_BASE_URL}/locations"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("locations", [])
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout fetching locations from Safe Swim API")
            raise SafeSwimAPIConnectionError(
                "Timeout connecting to Safe Swim API"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching locations from Safe Swim API: %s", err)
            raise SafeSwimAPIConnectionError(
                f"Error connecting to Safe Swim API: {err}"
            ) from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching locations: %s", err)
            raise SafeSwimAPIError(f"Unexpected error: {err}") from err

    async def get_location_forecast(self, slug: str) -> dict[str, Any] | None:
        """Fetch forecast data for a specific location.
        
        Args:
            slug: The location slug (e.g., 'rothesay-bay')
            
        Returns:
            Dictionary with location details and forecast data, or None if not found.
            
        Raises:
            SafeSwimAPIConnectionError: If unable to connect to API.
            SafeSwimAPIError: For other API errors.
        """
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with self._session.get(
                    f"{API_BASE_URL}/locations/{slug}"
                ) as response:
                    if response.status == 404:
                        _LOGGER.warning("Location %s not found", slug)
                        return None
                    response.raise_for_status()
                    return await response.json()
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout fetching forecast for %s", slug)
            raise SafeSwimAPIConnectionError(
                f"Timeout fetching forecast for {slug}"
            ) from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching forecast for %s: %s", slug, err)
            raise SafeSwimAPIConnectionError(
                f"Error fetching forecast for {slug}: {err}"
            ) from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching forecast for %s: %s", slug, err)
            raise SafeSwimAPIError(f"Unexpected error: {err}") from err
