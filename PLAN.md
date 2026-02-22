# Safe Swim Home Assistant Integration - Implementation Plan

## Overview
Create a Home Assistant integration to track and display water quality and weather data from https://safeswim.org.nz/ for New Zealand beaches and swimming locations.

## API Analysis

### Evidence: API Endpoint Structure
Based on inspection using curl:

**Locations API** (`https://safeswim.org.nz/api/locations`):
- Returns list of all available beach locations
- Each location includes: name, slug, position [lat, lng], patrolled status, and current water quality state
- ~200+ locations available across New Zealand

**Location Forecast API** (`https://safeswim.org.nz/api/locations/{slug}`):
- Returns detailed forecast data for a specific location
- Includes 72-hour forecast arrays (hourly data) for:
  - **WATER_QUALITY**: GREEN/GREY/RED/RED+/BLACK status values (validated across multiple locations)
    - GREEN: Good water quality, safe for swimming
    - GREY: Uncertain quality, no recent testing data
    - RED: Poor quality, swimming not advised
    - RED+: Permanently poor quality (streams/rivers with consistent issues)
    - BLACK: Very poor quality, do not swim
    - null: No data available for this location
  - **WATER_TEMPERATURE**: Celsius values as strings
  - **ATMOSPHERIC_TEMPERATURE**: Air temperature in Celsius
  - **TIDE**: Format "height:minutes" or null (e.g., "2.76:24" = 2.76m at 24 minutes past the hour)
  - **UV_INDEX**: Integer values as strings (0-11+)
  - **WEATHER_CONDITIONS**: SUN/CLOUD values (validated - only these two values observed)
  - **WIND_DIRECTION**: Degrees as strings (0-360)
  - **WIND_SPEED**: km/h as strings
- Location metadata: description, latitude, longitude, tags (facilities/hazards), images, alerts, patrols

## Integration Architecture

### Integration Type
**Type**: `service` (provides access to a single cloud service)
**IoT Class**: `cloud_polling` (requires internet, polls data periodically)

### File Structure
```
custom_components/safeswim/
├── __init__.py              # Integration setup, coordinator initialization
├── manifest.json            # Integration metadata and dependencies
├── config_flow.py          # User configuration flow (location selection)
├── const.py                # Constants and configuration keys
├── coordinator.py          # DataUpdateCoordinator for API polling
├── sensor.py               # Sensor platform with entity definitions
├── api.py                  # API client wrapper
├── translations/
│   └── en.json            # UI strings for config flow
└── strings.json           # Configuration flow strings
```

## Implementation Details

### 1. manifest.json
```json
{
  "domain": "safeswim",
  "name": "Safe Swim",
  "codeowners": [],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/...",
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0"
}
```

**Rationale**: 
- No special dependencies beyond standard aiohttp
- Config flow enables UI-based configuration
- Cloud polling as data is fetched from external API

### 2. const.py
Define constants:
```python
DOMAIN = "safeswim"
CONF_LOCATION_SLUG = "location_slug"
CONF_LOCATION_NAME = "location_name"
DEFAULT_UPDATE_INTERVAL = 1800  # 30 minutes
API_BASE_URL = "https://safeswim.org.nz/api"
```

**Sensor Types** (for each forecast type):
- Water Quality (quality status)
- Water Temperature (°C)
- Air Temperature (°C)
- Tide (height in meters, time)
- UV Index (0-11+)
- Weather Conditions (sun/cloud)
- Wind Direction (degrees)
- Wind Speed (km/h)

### 3. api.py - API Client
**Responsibilities**:
- Fetch locations list
- Fetch specific location forecast data
- Handle HTTP errors gracefully
- Parse JSON responses
- Async operations using aiohttp

**Key Methods**:
```python
class SafeSwimAPI:
    async def get_locations() -> list[dict]
    async def get_location_forecast(slug: str) -> dict
    async def close()  # Clean up aiohttp session
```

**Error Handling**:
- Network timeouts (10 second timeout)
- HTTP errors (404, 500, etc.)
- JSON parsing errors
- Return None on error, let coordinator handle retry logic

### 4. config_flow.py - Configuration Flow
**User Flow**:
1. User adds integration via UI
2. System fetches list of locations from API
3. User selects location from dropdown (sorted alphabetically)
4. Config entry created with location slug and name

**Features**:
- Unique ID: Use location slug as unique ID to prevent duplicates
- Validation: Ensure location exists in API
- Error handling: Display error if API is unavailable
- Reconfigure: Allow changing location selection

**Step Implementation**:
```python
async def async_step_user(self, user_input):
    """Handle user initiated configuration"""
    # 1. Fetch locations from API
    # 2. Show form with location selector
    # 3. Validate selection
    # 4. Set unique ID based on slug
    # 5. Create config entry with slug and name
```

### 5. coordinator.py - Data Update Coordinator
**Purpose**: Centralized data fetching for all sensors

**Update Strategy**:
- Poll every 30 minutes (configurable)
- Fetch forecast once, distribute to all sensor entities
- Handle API failures gracefully with retry logic
- Only update if there are listeners (automatic via coordinator)

**Data Structure**:
```python
{
    "location": {
        "name": str,
        "latitude": float,
        "longitude": float,
        "description": str,
        "patrolled": bool,
        "tags": list[dict],
    },
    "forecasts": {
        "WATER_QUALITY": list[str],  # 72 hourly values
        "WATER_TEMPERATURE": list[str],
        "ATMOSPHERIC_TEMPERATURE": list[str],
        "TIDE": list[str | None],
        "UV_INDEX": list[str],
        "WEATHER_CONDITIONS": list[str],
        "WIND_DIRECTION": list[str],
        "WIND_SPEED": list[str],
    },
    "alerts": list[dict],
    "last_update": datetime,
}
```

**Error Handling**:
- Raise `UpdateFailed` on API errors
- Raise `ConfigEntryAuthFailed` if API is permanently unavailable
- Automatic exponential backoff via coordinator

### 6. __init__.py - Integration Setup
**Responsibilities**:
- Create API client instance
- Initialize coordinator with API client
- Store coordinator in hass.data
- Forward setup to sensor platform
- Handle unload cleanup

```python
async def async_setup_entry(hass, entry):
    """Set up Safe Swim from a config entry"""
    # 1. Create API client
    # 2. Create coordinator with client
    # 3. Perform initial data fetch
    # 4. Store coordinator in hass.data[DOMAIN][entry.entry_id]
    # 5. Forward entry setup to sensor platform
    # 6. Return True

async def async_unload_entry(hass, entry):
    """Unload a config entry"""
    # 1. Unload sensor platform
    # 2. Close API client
    # 3. Remove from hass.data
    # 4. Return True
```

### 7. sensor.py - Sensor Entities
**Device Structure**:
- One device per location
- Device info includes: name, location coordinates, manufacturer="Safe Swim"

**Sensor Entities** (8-9 entities per location):

1. **Water Quality Sensor**
   - Entity ID: `sensor.safeswim_{location}_water_quality`
   - State: Current hour's quality (GREEN/GREY/RED/RED+/BLACK)
   - Icon: Dynamic based on state:
     - GREEN: mdi:water (good)
     - GREY: mdi:water-alert (uncertain)
     - RED: mdi:water-minus (poor)
     - RED+: mdi:water-remove (permanently poor)
     - BLACK: mdi:water-off (do not swim)
   - Attributes: 
     - Next 24 hours forecast
     - Description text mapping:
       - GREEN: "Good water quality - safe for swimming"
       - GREY: "Uncertain quality - no recent testing"
       - RED: "Poor quality - swimming not advised"
       - RED+: "Permanently poor quality"
       - BLACK: "Very poor quality - do not swim"

2. **Water Temperature Sensor**
   - Entity ID: `sensor.safeswim_{location}_water_temperature`
   - Device Class: `temperature`
   - State Class: `measurement`
   - Native Unit: °C
   - State: Current water temperature
   - Attributes: Forecast for next 24 hours

3. **Air Temperature Sensor**
   - Entity ID: `sensor.safeswim_{location}_air_temperature`
   - Device Class: `temperature`
   - State Class: `measurement`
   - Native Unit: °C
   - State: Current air temperature

4. **Tide Sensor**
   - Entity ID: `sensor.safeswim_{location}_tide`
   - State: Current/next tide event description
   - Unit: meters
   - Attributes:
     - Tide height (parsed from "height:minutes")
     - Tide time (calculated from array index + minutes)
     - Next high and low tides with times

5. **UV Index Sensor**
   - Entity ID: `sensor.safeswim_{location}_uv_index`
   - State: Current UV index (integer)
   - Icon: mdi:weather-sunny-alert (when high)
   - Attributes: Protection recommendation based on value

6. **Weather Conditions Sensor**
   - Entity ID: `sensor.safeswim_{location}_weather`
   - State: Current weather (Sunny/Cloudy)
   - Icon: mdi:weather-sunny or mdi:weather-cloudy

7. **Wind Direction Sensor**
   - Entity ID: `sensor.safeswim_{location}_wind_direction`
   - State: Wind direction in degrees
   - Native Unit: °
   - Attributes: Compass direction (N, NE, E, SE, etc.)

8. **Wind Speed Sensor**
   - Entity ID: `sensor.safeswim_{location}_wind_speed`
   - Device Class: `wind_speed`
   - State Class: `measurement`
   - Native Unit: km/h
   - State: Current wind speed

9. **Location Info Sensor** (Diagnostic)
   - Entity ID: `sensor.safeswim_{location}_info`
   - Entity Category: `diagnostic`
   - State: "Active" or "Patrolled" status
   - Attributes:
     - Description
     - Facilities (from tags)
     - Hazards (from tags)
     - Active alerts
     - Patrol times

**Entity Base Class**:
```python
class SafeSwimEntity(CoordinatorEntity):
    """Base class for Safe Swim entities"""
    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Safe Swim"
    
    def __init__(self, coordinator, location_slug, entity_description):
        super().__init__(coordinator)
        self._location_slug = location_slug
        self.entity_description = entity_description
        
    @property
    def device_info(self):
        """Return device info for grouping entities"""
        return {
            "identifiers": {(DOMAIN, self._location_slug)},
            "name": self.coordinator.data["location"]["name"],
            "manufacturer": "Safe Swim",
            "model": "Beach Location",
            "configuration_url": f"https://safeswim.org.nz/locations/{self._location_slug}",
        }
```

**Sensor Subclasses**:
Each sensor type will extend `SafeSwimSensor(SafeSwimEntity, SensorEntity)` and implement:
- `native_value` property: Extract current value from coordinator data
- `extra_state_attributes` property: Add forecast and additional info
- Entity description with appropriate device class, unit, icon

### 8. Data Flow

```
User adds integration
    ↓
Config flow fetches locations → User selects location
    ↓
async_setup_entry creates API client and coordinator
    ↓
Coordinator performs initial data fetch
    ↓
Sensor platform creates 11 sensor entities
    ↓
[Every 30 minutes]
    ↓
Coordinator fetches fresh data from API
    ↓
Entities automatically update via CoordinatorEntity
    ↓
Home Assistant state machine updated
```

### 9. Testing Strategy

**Manual Testing**:
1. Verify locations list loads in config flow
2. Test location selection and config entry creation
3. Verify all sensors created with correct values
4. Check entity attributes contain forecast data
5. Test reload/reconfigure functionality
6. Verify graceful handling of API downtime
7. Check device grouping in UI

**API Scenarios**:
- API returns valid data: All sensors update correctly
- API returns null values: Sensors show "unavailable"
- API timeout: Coordinator retries with backoff
- API returns 404: Config flow shows error
- Network offline: Sensors show "unavailable", automatic retry

### 10. Configuration Options

**Initial Config**:
- Location selection (required)

**Future Enhancements** (not in v1):
- Update interval configuration
- Which sensors to enable/disable
- Alert notifications setup
- Multiple locations in single config entry

### 11. Implementation Order

**Phase 1: Core Infrastructure**
1. Create file structure and manifest.json
2. Implement const.py with all constants
3. Build api.py with aiohttp client
4. Test API client with curl commands

**Phase 2: Configuration**
5. Implement config_flow.py
6. Create translations/strings.json
7. Test config flow in Home Assistant

**Phase 3: Data Coordination**
8. Implement coordinator.py
9. Implement __init__.py with entry setup
10. Test coordinator data fetching

**Phase 4: Sensors**
11. Create sensor entity base classes
12. Implement each sensor type (11 sensors)
13. Test sensor entities and attributes

**Phase 5: Polish**
14. Add comprehensive error handling
15. Add logging at appropriate levels
16. Test reload/reconfigure flows
17. Verify device info and entity registry
18. Write documentation

## Technical Decisions and Rationale

### Why DataUpdateCoordinator?
- **Evidence**: Multiple entities need same data source
- **Benefit**: Single API call fetches data for all 11 sensors
- **Efficiency**: Reduces API load, improves response time
- **Pattern**: Standard HA pattern for multi-entity integrations

### Why Config Flow?
- **User Experience**: UI-based setup is more accessible
- **Validation**: Can validate location exists before creating entry
- **Multiple Locations**: Users can add multiple beach locations easily
- **Modern Standard**: New integrations should use config entries

### Why 30-minute Updates?
- **Forecast Horizon**: 72-hour forecast is long-term data
- **API Consideration**: Reduces unnecessary load on Safe Swim API
- **Battery/Resource**: Mobile users benefit from less frequent updates
- **Configurable**: Can be adjusted if needed

### Data Type Conversions
- API returns strings → Convert to appropriate Python types
- Temperature: string → float
- UV Index: string → int
- Tide: "height:minutes" → parse to float (height) + time calculation
- Wind: strings → float/int as appropriate

### Entity Categories
- Main sensors (water quality, temperature, etc.): No category (user-facing)
- Location info: `diagnostic` category (less prominent in UI)

## Potential Issues and Mitigations

### Issue: API Changes
- **Mitigation**: Defensive parsing with try/except
- **Fallback**: Return None for unavailable data
- **Logging**: Log unexpected data formats

### Issue: Location Slug Changes
- **Mitigation**: Unique ID based on slug prevents duplicates
- **Recovery**: User can delete and re-add if slug changes

### Issue: Large Forecast Arrays
- **Mitigation**: Only store relevant data in attributes (24 hours)
- **Performance**: Coordinator handles parsing once for all entities

### Issue: Timezone Handling
- **Mitigation**: API appears to use NZ time, document this assumption
- **Attributes**: Include timestamp with timezone info

### Issue: Null Values in Forecasts
- **Mitigation**: Check for None before parsing
- **State**: Set sensor to "unavailable" if current value is None

## Success Criteria

1. ✅ User can discover and add integration via UI
2. ✅ User can select from list of 200+ NZ beaches
3. ✅ All 11 sensor entities created per location
4. ✅ Sensors update every 30 minutes automatically
5. ✅ Device grouping shows all sensors together in UI
6. ✅ Forecast data available in sensor attributes
7. ✅ Graceful error handling when API is down
8. ✅ Sensors show "unavailable" when data is missing
9. ✅ Integration can be reloaded without errors
10. ✅ Multiple locations can be configured simultaneously

## Future Enhancements (Post v1.0)

1. **Alert Notifications**: Push notifications for water quality alerts
2. **Patrol Schedule**: Display lifeguard patrol times
3. **Webcam Integration**: camera platform if camId available
4. **Historical Data**: Store and graph historical water quality
5. **Favorable Conditions**: Binary sensor for "good swimming conditions"
6. **Distance Calculation**: Show nearest beaches based on home location
7. **Tide Predictions**: Better tide time calculations and high/low identification
8. **Weather Integration**: Combine with HA weather data for better forecasts

## Notes and Assumptions

- API is public and doesn't require authentication
- No rate limiting observed in testing
- Data is specific to New Zealand locations
- Forecast arrays contain 72 hourly values (3 days)
- Array index represents hours from current time
- Tide format "height:minutes" needs parsing
- Quality values (validated from live API data):
  - GREEN: Good water quality, safe for swimming
  - GREY: Uncertain/no recent testing
  - RED: Poor quality, swimming not advised
  - RED+: Permanently poor quality (typically streams/rivers)
  - BLACK: Very poor quality, do not swim
  - null: No data available
- Weather conditions (validated): Only SUN and CLOUD observed
- API appears stable and maintained by Auckland Council
- No terms of service restrictions found for non-commercial use

---

## Installation Instructions

### Method 1: Manual Installation (Recommended for Development)

1. **Locate your Home Assistant configuration directory**:
   - Usually `/config` when running in Docker/Home Assistant OS
   - Or `~/.homeassistant` for manual installations
   - Find it via: Settings → System → Repairs → Three dots menu → System information → "Configuration directory"

2. **Create the custom_components directory** (if it doesn't exist):
   ```bash
   mkdir -p /config/custom_components
   ```

3. **Copy the integration files**:
   ```bash
   # From your development directory
   cp -r custom_components/safeswim /config/custom_components/
   ```

   Your directory structure should look like:
   ```
   /config/
   └── custom_components/
       └── safeswim/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── sensor.py
           ├── api.py
           ├── strings.json
           └── translations/
               └── en.json
   ```

4. **Restart Home Assistant**:
   - Settings → System → Restart
   - Or via command line: `ha core restart` (HA OS) or `docker restart homeassistant`

5. **Add the integration**:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Safe Swim"
   - Follow the configuration flow to select your beach location

### Method 2: HACS Installation (Future)

Once the integration is published to HACS:

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add the repository URL
5. Search for "Safe Swim" and install
6. Restart Home Assistant
7. Add the integration via Settings → Devices & Services

### Method 3: Git Clone (for Active Development)

1. **SSH/Terminal into your Home Assistant host**

2. **Navigate to custom_components directory**:
   ```bash
   cd /config/custom_components
   ```

3. **Clone the repository** (or create a symlink):
   ```bash
   git clone https://github.com/yourusername/ha-safeswim.git safeswim
   ```
   
   Or create a symlink from your development directory:
   ```bash
   ln -s /path/to/your/development/custom_components/safeswim /config/custom_components/safeswim
   ```

4. **Restart and configure** (as above)

### Verification

1. **Check logs for errors**:
   - Settings → System → Logs
   - Look for entries containing `safeswim`

2. **Verify entities were created**:
   - Settings → Devices & Services → Safe Swim
   - Click on the location device
   - Should see 11 sensor entities

3. **Check entity states**:
   - Developer Tools → States
   - Search for `sensor.safeswim_`
   - Verify entities have valid states and attributes

### Troubleshooting

**Integration not appearing in Add Integration list:**
- Verify `manifest.json` is valid JSON
- Check file permissions (should be readable)
- Ensure `domain` in manifest matches directory name
- Restart Home Assistant again
- Check logs for manifest validation errors

**Config flow errors:**
- Check Home Assistant logs for Python exceptions
- Verify API is accessible: `curl https://safeswim.org.nz/api/locations`
- Check network connectivity from HA instance

**Entities not updating:**
- Check coordinator logs for update errors
- Verify API endpoint returns data for selected location
- Check update interval in coordinator settings

**"Unknown" or "Unavailable" states:**
- Check if API returned null values for that forecast type
- Some locations may not have all forecast types (e.g., tide data)
- Review entity attributes for raw data

### Updating the Integration

**Manual installation:**
```bash
# Backup existing (optional)
cp -r /config/custom_components/safeswim /config/custom_components/safeswim.backup

# Copy new files
cp -r custom_components/safeswim /config/custom_components/

# Restart Home Assistant
ha core restart
```

**Git installation:**
```bash
cd /config/custom_components/safeswim
git pull
ha core restart
```

**HACS installation:**
- HACS will notify you of updates automatically
- Click "Update" in HACS
- Restart Home Assistant

---

**Implementation Timeline**: 8-12 hours for v1.0 (experienced HA developer)

**Testing Environment**: Home Assistant 2024.1+ with Python 3.11+
