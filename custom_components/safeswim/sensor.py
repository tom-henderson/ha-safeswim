"""Sensor platform for Safe Swim integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.util import dt as dt_util

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_LOCATION_SLUG,
    DOMAIN,
    FORECAST_ATMOSPHERIC_TEMPERATURE,
    FORECAST_TIDE,
    FORECAST_UV_INDEX,
    FORECAST_WATER_QUALITY,
    FORECAST_WATER_TEMPERATURE,
    FORECAST_WEATHER_CONDITIONS,
    FORECAST_WIND_DIRECTION,
    FORECAST_WIND_SPEED,
    WATER_QUALITY_BLACK,
    WATER_QUALITY_DESCRIPTIONS,
    WATER_QUALITY_GREEN,
    WATER_QUALITY_GREY,
    WATER_QUALITY_RED,
    WATER_QUALITY_RED_PLUS,
    WEATHER_CLOUD,
    WEATHER_SUN,
)
from .coordinator import SafeSwimCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SafeSwimSensorEntityDescription(SensorEntityDescription):
    """Describes Safe Swim sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] = None
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] = None


def get_current_forecast_value(
    forecasts: dict[str, list], forecast_type: str
) -> Any | None:
    """Get the current (first) value from a forecast array."""
    if forecast_type not in forecasts:
        return None
    values = forecasts[forecast_type]
    if not values or len(values) == 0:
        return None
    return values[0]


def get_forecast_values(
    forecasts: dict[str, list], forecast_type: str, count: int = 24
) -> list[Any]:
    """Get upcoming forecast values."""
    if forecast_type not in forecasts:
        return []
    values = forecasts[forecast_type]
    return [v for v in values[:count] if v is not None]


def parse_tide_value(tide_str: str | None) -> dict[str, Any] | None:
    """Parse tide string format 'height:minutes'.
    
    Args:
        tide_str: String like "2.76:24" meaning 2.76m at 24 minutes past the hour
        
    Returns:
        Dictionary with height and minutes, or None if invalid
    """
    if not tide_str or tide_str == "null":
        return None
    
    try:
        parts = tide_str.split(":")
        if len(parts) == 2:
            height = float(parts[0])
            minutes = int(parts[1])
            return {"height": height, "minutes": minutes}
    except (ValueError, AttributeError):
        _LOGGER.debug("Unable to parse tide value: %s", tide_str)
    
    return None


def parse_tide_events(forecasts: dict[str, list]) -> list[dict[str, Any]]:
    """Extract tide events from forecast data.
    
    Args:
        forecasts: Forecast data dictionary
        
    Returns:
        List of tide events with index, height, minutes, and datetime
    """
    if FORECAST_TIDE not in forecasts:
        return []
    
    tide_values = forecasts[FORECAST_TIDE]
    events = []
    # API uses NZ local time (Pacific/Auckland)
    now = dt_util.now(ZoneInfo("Pacific/Auckland"))
    
    for idx, tide_str in enumerate(tide_values):
        if tide_str:
            parsed = parse_tide_value(tide_str)
            if parsed:
                # Calculate actual datetime of tide event
                tide_time = now + timedelta(hours=idx, minutes=parsed["minutes"])
                events.append({
                    "index": idx,
                    "height": parsed["height"],
                    "minutes": parsed["minutes"],
                    "time": tide_time,
                })
    
    return events


def get_tide_direction(tide_events: list[dict[str, Any]]) -> str | None:
    """Determine current tide direction.
    
    Args:
        tide_events: List of tide events from parse_tide_events()
        
    Returns:
        'RISING', 'FALLING', 'HIGH', 'LOW', or None
    """
    if not tide_events:
        return None
    
    # Threshold to distinguish high vs low tide (in meters)
    HIGH_TIDE_THRESHOLD = 1.5
    
    # Find the most recent past event and next future event
    # API uses NZ local time (Pacific/Auckland)
    now = dt_util.now(ZoneInfo("Pacific/Auckland"))
    prev_event = None
    next_event = None
    
    for event in tide_events:
        if event["time"] <= now:
            prev_event = event
        elif next_event is None:
            next_event = event
            break
    
    # If we're very close to an event (within 15 minutes), show HIGH or LOW
    if next_event and abs((next_event["time"] - now).total_seconds()) < 900:  # 15 min
        return "HIGH" if next_event["height"] > HIGH_TIDE_THRESHOLD else "LOW"
    
    if prev_event and abs((now - prev_event["time"]).total_seconds()) < 900:  # 15 min
        return "HIGH" if prev_event["height"] > HIGH_TIDE_THRESHOLD else "LOW"
    
    # Determine direction based on next event
    if next_event:
        if prev_event:
            # We have both - compare heights to determine direction
            if next_event["height"] > prev_event["height"]:
                return "RISING"
            else:
                return "FALLING"
        else:
            # Only have next event - if it's high, we're rising; if low, we're falling
            return "RISING" if next_event["height"] > HIGH_TIDE_THRESHOLD else "FALLING"
    
    return None


def find_next_high_tide(tide_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the next high tide event.
    
    Args:
        tide_events: List of tide events from parse_tide_events()
        
    Returns:
        Dictionary with time and height, or None if not found
    """
    if not tide_events:
        return None
    
    HIGH_TIDE_THRESHOLD = 1.5
    # API uses NZ local time (Pacific/Auckland)
    now = dt_util.now(ZoneInfo("Pacific/Auckland"))
    
    for event in tide_events:
        if event["time"] > now and event["height"] > HIGH_TIDE_THRESHOLD:
            return {
                "time": event["time"],
                "height": event["height"],
            }
    
    return None


def find_next_low_tide(tide_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the next low tide event.
    
    Args:
        tide_events: List of tide events from parse_tide_events()
        
    Returns:
        Dictionary with time and height, or None if not found
    """
    if not tide_events:
        return None
    
    HIGH_TIDE_THRESHOLD = 1.5
    # API uses NZ local time (Pacific/Auckland)
    now = dt_util.now(ZoneInfo("Pacific/Auckland"))
    
    for event in tide_events:
        if event["time"] > now and event["height"] <= HIGH_TIDE_THRESHOLD:
            return {
                "time": event["time"],
                "height": event["height"],
            }
    
    return None


def get_compass_direction(degrees: float) -> str:
    """Convert wind direction degrees to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


# Sensor entity descriptions
SENSOR_TYPES: tuple[SafeSwimSensorEntityDescription, ...] = (
    SafeSwimSensorEntityDescription(
        key="water_quality",
        translation_key="water_quality",
        icon="mdi:water",
        value_fn=lambda data: get_current_forecast_value(
            data["forecasts"], FORECAST_WATER_QUALITY
        ),
        attributes_fn=lambda data: {
            "forecast_24h": get_forecast_values(
                data["forecasts"], FORECAST_WATER_QUALITY, 24
            ),
            "description": WATER_QUALITY_DESCRIPTIONS.get(
                get_current_forecast_value(
                    data["forecasts"], FORECAST_WATER_QUALITY
                )
            ),
        },
    ),
    SafeSwimSensorEntityDescription(
        key="water_temperature",
        translation_key="water_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: (
            float(val)
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_WATER_TEMPERATURE
            )) is not None
            else None
        ),
        attributes_fn=lambda data: {
            "forecast_24h": [
                float(v) for v in get_forecast_values(
                    data["forecasts"], FORECAST_WATER_TEMPERATURE, 24
                ) if v
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="air_temperature",
        translation_key="air_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: (
            float(val)
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_ATMOSPHERIC_TEMPERATURE
            )) is not None
            else None
        ),
        attributes_fn=lambda data: {
            "forecast_24h": [
                float(v) for v in get_forecast_values(
                    data["forecasts"], FORECAST_ATMOSPHERIC_TEMPERATURE, 24
                ) if v
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="tide_direction",
        translation_key="tide_direction",
        icon="mdi:waves",
        value_fn=lambda data: get_tide_direction(
            parse_tide_events(data["forecasts"])
        ),
        attributes_fn=lambda data: {
            "tide_events": [
                {
                    "time": event["time"].isoformat(),
                    "height": event["height"],
                    "type": "HIGH" if event["height"] > 1.5 else "LOW",
                }
                for event in parse_tide_events(data["forecasts"])[:6]
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="next_high_tide",
        translation_key="next_high_tide",
        icon="mdi:arrow-up-bold",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            next_high["time"]
            if (next_high := find_next_high_tide(
                parse_tide_events(data["forecasts"])
            ))
            else None
        ),
        attributes_fn=lambda data: {
            "height": (
                next_high["height"]
                if (next_high := find_next_high_tide(
                    parse_tide_events(data["forecasts"])
                ))
                else None
            ),
        },
    ),
    SafeSwimSensorEntityDescription(
        key="next_low_tide",
        translation_key="next_low_tide",
        icon="mdi:arrow-down-bold",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: (
            next_low["time"]
            if (next_low := find_next_low_tide(
                parse_tide_events(data["forecasts"])
            ))
            else None
        ),
        attributes_fn=lambda data: {
            "height": (
                next_low["height"]
                if (next_low := find_next_low_tide(
                    parse_tide_events(data["forecasts"])
                ))
                else None
            ),
        },
    ),
    SafeSwimSensorEntityDescription(
        key="uv_index",
        translation_key="uv_index",
        icon="mdi:weather-sunny-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            int(val)
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_UV_INDEX
            )) is not None
            else None
        ),
        attributes_fn=lambda data: {
            "forecast_24h": [
                int(v) for v in get_forecast_values(
                    data["forecasts"], FORECAST_UV_INDEX, 24
                ) if v
            ],
            "protection_recommendation": (
                "Seek shade, wear protective clothing"
                if (uv := get_current_forecast_value(
                    data["forecasts"], FORECAST_UV_INDEX
                )) and int(uv) >= 6
                else "Normal sun protection recommended"
                if uv and int(uv) >= 3
                else "No protection needed"
            ),
        },
    ),
    SafeSwimSensorEntityDescription(
        key="weather",
        translation_key="weather",
        value_fn=lambda data: (
            "Sunny" if val == WEATHER_SUN else "Cloudy"
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_WEATHER_CONDITIONS
            ))
            else None
        ),
        attributes_fn=lambda data: {
            "forecast_24h": [
                "Sunny" if v == WEATHER_SUN else "Cloudy"
                for v in get_forecast_values(
                    data["forecasts"], FORECAST_WEATHER_CONDITIONS, 24
                )
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="wind_direction",
        translation_key="wind_direction",
        icon="mdi:compass",
        value_fn=lambda data: (
            get_compass_direction(int(val))
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_WIND_DIRECTION
            )) is not None
            else None
        ),
        attributes_fn=lambda data: {
            "degrees": (
                int(val)
                if (val := get_current_forecast_value(
                    data["forecasts"], FORECAST_WIND_DIRECTION
                ))
                else None
            ),
            "forecast_24h": [
                {
                    "degrees": int(v),
                    "direction": get_compass_direction(int(v)),
                }
                for v in get_forecast_values(
                    data["forecasts"], FORECAST_WIND_DIRECTION, 24
                ) if v
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="wind_speed",
        translation_key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        suggested_display_precision=0,
        value_fn=lambda data: (
            int(val)
            if (val := get_current_forecast_value(
                data["forecasts"], FORECAST_WIND_SPEED
            )) is not None
            else None
        ),
        attributes_fn=lambda data: {
            "forecast_24h": [
                int(v) for v in get_forecast_values(
                    data["forecasts"], FORECAST_WIND_SPEED, 24
                ) if v
            ],
        },
    ),
    SafeSwimSensorEntityDescription(
        key="location_info",
        translation_key="location_info",
        icon="mdi:information",
        entity_registry_enabled_default=False,
        value_fn=lambda data: (
            "Patrolled" if data["location"]["patrolled"] else "Not Patrolled"
        ),
        attributes_fn=lambda data: {
            "description": data["location"].get("description"),
            "latitude": data["location"].get("latitude"),
            "longitude": data["location"].get("longitude"),
            "facilities": [
                tag["name"]
                for tag in data["location"].get("tags", [])
                if tag.get("type") == "LOCATION_FACILITY"
            ],
            "hazards": [
                tag["name"]
                for tag in data["location"].get("tags", [])
                if tag.get("type") == "LOCATION_HAZARD"
            ],
            "alerts": [
                alert.get("message") for alert in data.get("alerts", [])
            ],
            "patrols": data.get("patrols", []),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Safe Swim sensor entities."""
    coordinator: SafeSwimCoordinator = hass.data[DOMAIN][entry.entry_id]
    location_slug = entry.data[CONF_LOCATION_SLUG]

    entities = [
        SafeSwimSensor(coordinator, location_slug, description)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class SafeSwimSensor(CoordinatorEntity[SafeSwimCoordinator], SensorEntity):
    """Representation of a Safe Swim sensor."""

    entity_description: SafeSwimSensorEntityDescription
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: SafeSwimCoordinator,
        location_slug: str,
        description: SafeSwimSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._location_slug = location_slug
        self._attr_unique_id = f"{location_slug}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this entity."""
        location = self.coordinator.data["location"]
        return {
            "identifiers": {(DOMAIN, self._location_slug)},
            "name": location["name"],
            "manufacturer": "Safe Swim",
            "model": "Beach Location",
            "configuration_url": f"https://safeswim.org.nz/locations/{self._location_slug}",
        }

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor based on state."""
        # Dynamic icon for water quality sensor
        if self.entity_description.key == "water_quality":
            quality = self.native_value
            if quality == WATER_QUALITY_GREEN:
                return "mdi:water"
            elif quality == WATER_QUALITY_GREY:
                return "mdi:water-alert"
            elif quality == WATER_QUALITY_RED:
                return "mdi:water-minus"
            elif quality == WATER_QUALITY_RED_PLUS:
                return "mdi:water-remove"
            elif quality == WATER_QUALITY_BLACK:
                return "mdi:water-off"
        
        # Dynamic icon for tide direction sensor
        elif self.entity_description.key == "tide_direction":
            direction = self.native_value
            if direction == "RISING":
                return "mdi:wave-arrow-up"
            elif direction == "FALLING":
                return "mdi:wave-arrow-down"
            elif direction == "HIGH":
                return "mdi:waves"
            elif direction == "LOW":
                return "mdi:wave"
        
        # Dynamic icon for weather sensor
        elif self.entity_description.key == "weather":
            if self.native_value == "Sunny":
                return "mdi:weather-sunny"
            elif self.native_value == "Cloudy":
                return "mdi:weather-cloudy"
        
        # Default icon from description
        return self.entity_description.icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.entity_description.attributes_fn:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None
