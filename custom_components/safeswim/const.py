"""Constants for the Safe Swim integration."""

DOMAIN = "safeswim"

# Configuration
CONF_LOCATION_SLUG = "location_slug"
CONF_LOCATION_NAME = "location_name"

# API
API_BASE_URL = "https://safeswim.org.nz/api"
API_TIMEOUT = 10

# Update interval (seconds)
DEFAULT_UPDATE_INTERVAL = 1800  # 30 minutes

# Water quality states
WATER_QUALITY_GREEN = "GREEN"
WATER_QUALITY_GREY = "GREY"
WATER_QUALITY_RED = "RED"
WATER_QUALITY_RED_PLUS = "RED+"
WATER_QUALITY_BLACK = "BLACK"

# Water quality descriptions
WATER_QUALITY_DESCRIPTIONS = {
    WATER_QUALITY_GREEN: "Good water quality - safe for swimming",
    WATER_QUALITY_GREY: "Uncertain quality - no recent testing",
    WATER_QUALITY_RED: "Poor quality - swimming not advised",
    WATER_QUALITY_RED_PLUS: "Permanently poor quality",
    WATER_QUALITY_BLACK: "Very poor quality - do not swim",
}

# Weather conditions
WEATHER_SUN = "SUN"
WEATHER_CLOUD = "CLOUD"

# Forecast types
FORECAST_WATER_QUALITY = "WATER_QUALITY"
FORECAST_WATER_TEMPERATURE = "WATER_TEMPERATURE"
FORECAST_ATMOSPHERIC_TEMPERATURE = "ATMOSPHERIC_TEMPERATURE"
FORECAST_TIDE = "TIDE"
FORECAST_UV_INDEX = "UV_INDEX"
FORECAST_WEATHER_CONDITIONS = "WEATHER_CONDITIONS"
FORECAST_WIND_DIRECTION = "WIND_DIRECTION"
FORECAST_WIND_SPEED = "WIND_SPEED"

# Attribution
ATTRIBUTION = "Data provided by Safe Swim"
