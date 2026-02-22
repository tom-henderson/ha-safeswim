# Safe Swim - Home Assistant Integration

A Home Assistant integration to track and display water quality and weather data from [Safe Swim](https://safeswim.org.nz/) for New Zealand beaches and swimming locations.

## Features

- 🏖️ **200+ Locations**: Monitor any beach or swimming spot in New Zealand covered by Safe Swim
- 🗺️ **Map Display**: All beach locations appear on the Home Assistant map with color-coded water quality icons
- 🌊 **Water Quality**: Real-time water quality status (GREEN/GREY/RED/RED+/BLACK)
- 🌡️ **Temperature Monitoring**: Both water and air temperature tracking
- 🌊 **Tide Information**: Current tide levels and upcoming tide events
- ☀️ **UV Index**: Sun exposure monitoring with protection recommendations
- 🌤️ **Weather Conditions**: Current and forecasted weather
- 💨 **Wind Data**: Wind speed and direction with compass bearings
- 📊 **24-Hour Forecasts**: All sensors include 24-hour forecast data in attributes
- 11 sensor types per location

## Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Automation Examples](AUTOMATIONS.md)** - Comprehensive automation recipes and forecast usage
- **[Implementation Details](IMPLEMENTATION.md)** - Technical documentation for developers

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/safeswim` directory to your Home Assistant `config/custom_components/` directory:
   ```bash
   mkdir -p /config/custom_components
   cp -r custom_components/safeswim /config/custom_components/
   ```

2. Restart Home Assistant

3. Add the integration:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "Safe Swim"
   - Select your beach location from the dropdown

### Method 2: Git Clone (Development)

```bash
cd /config/custom_components
git clone https://github.com/yourusername/ha-safeswim.git safeswim
# Or create a symlink to your development directory
ln -s /path/to/your/dev/custom_components/safeswim /config/custom_components/safeswim
```

## Entities Created

For each location, the integration creates the following sensor entities:

| Entity | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| `sensor.safeswim_<location>_water_quality` | Water quality status | - | - |
| `sensor.safeswim_<location>_water_temperature` | Water temperature | °C | Temperature |
| `sensor.safeswim_<location>_air_temperature` | Air temperature | °C | Temperature |
| `sensor.safeswim_<location>_tide_direction` | Tide direction | - | - |
| `sensor.safeswim_<location>_next_high_tide` | Next high tide time | - | Timestamp |
| `sensor.safeswim_<location>_next_low_tide` | Next low tide time | - | Timestamp |
| `sensor.safeswim_<location>_uv_index` | UV index | - | - |
| `sensor.safeswim_<location>_weather` | Weather conditions | - | - |
| `sensor.safeswim_<location>_wind_direction` | Wind direction | - | - |
| `sensor.safeswim_<location>_wind_speed` | Wind speed | km/h | Wind Speed |
| `sensor.safeswim_<location>_location_info` | Location details | - | Diagnostic |

## Water Quality States

- **GREEN**: Good water quality - safe for swimming
- **GREY**: Uncertain quality - no recent testing
- **RED**: Poor quality - swimming not advised
- **RED+**: Permanently poor quality
- **BLACK**: Very poor quality - do not swim

## Entity Attributes

All sensors include additional forecast data in their attributes:

### Water Quality
```yaml
forecast_24h: [GREEN, GREEN, GREEN, ...]
description: "Good water quality - safe for swimming"
```

### Temperature Sensors
```yaml
forecast_24h: [22.4, 22.3, 22.3, ...]
```

### Tide Direction
```yaml
state: RISING  # or FALLING, HIGH, LOW
tide_events:
  - time: "2026-02-21T04:00:00+00:00"
    height: 0.34
    type: "LOW"
  - time: "2026-02-21T10:09:00+00:00"
    height: 2.79
    type: "HIGH"
```

### Next High/Low Tide
```yaml
state: "2026-02-21T10:09:00+00:00"  # Timestamp of tide event
height: 2.79  # Height in meters
```

### UV Index
```yaml
forecast_24h: [0, 0, 1, 2, 3, 4, ...]
protection_recommendation: "Normal sun protection recommended"
```

### Wind Direction
```yaml
state: "WSW"  # Compass direction (N, NE, E, SE, S, SW, W, NW, etc.)
degrees: 239  # Degrees for automations
forecast_24h:
  - degrees: 239
    direction: "WSW"
  - degrees: 237
    direction: "WSW"
  - degrees: 236
    direction: "WSW"
```

### Location Info
```yaml
description: "Full location description..."
latitude: -36.72137987
longitude: 174.7517965
facilities: ["Parking", "Toilet block", "Shower", ...]
hazards: ["Strong currents", "Unstable cliff", ...]
alerts: []
patrols: []
```

## 🗺️ Viewing Beaches on the Map

All beach locations automatically appear on the Home Assistant map with color-coded icons:

### Adding the Map Card

1. Go to any dashboard
2. Click **Edit Dashboard**
3. Click **+ Add Card**
4. Search for and select **Map**
5. Save

### Understanding the Map Icons

Each beach displays a colored circle indicating current water quality:
- � **Green circle with checkmark (✓)** = GREEN (safe for swimming)
- ⚪ **Grey circle with question mark (?)** = GREY (uncertain quality)
- 🔴 **Red circle** = RED (poor quality)
- 🔴 **Red circle with exclamation (!)** = RED+ (permanently poor quality)
- ⚫ **Black circle with X (×)** = BLACK (do not swim)

**Click any marker** to view:
- All current conditions (temperature, tide, wind, UV)
- 24-hour forecast data
- Full sensor details

### Tips

- Perfect for monitoring multiple beaches at a glance - instantly see water quality across all locations
- Icons update automatically every 30 minutes with the latest data
- The water quality sensor includes GPS coordinates in its attributes (`latitude`, `longitude`)
- Color-coded icons also appear in entity cards and more info dialogs

## Configuration

### Adding Multiple Locations

You can add multiple beach locations by adding the integration multiple times:
1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Safe Swim"
4. Select a different location

Each location creates a separate device with its own set of sensors.

### Reconfiguring a Location

To change the beach location for an existing configuration:
1. Go to **Settings** → **Devices & Services** → **Safe Swim**
2. Click on the device
3. Click **Configure**
4. Select a new location

## Update Frequency

The integration polls the Safe Swim API every **30 minutes** by default. This interval balances:
- Fresh data availability
- API server load considerations
- Home Assistant resource usage

## Automation Examples

> 💡 **See [AUTOMATIONS.md](AUTOMATIONS.md) for comprehensive examples** including tide-based alerts, forecast checking, beach condition scoring, and more advanced use cases.

### Send notification when water quality is poor

```yaml
automation:
  - alias: "Alert on poor water quality"
    trigger:
      - platform: state
        entity_id: sensor.safeswim_rothesay_bay_water_quality
        to: 
          - RED
          - RED+
          - BLACK
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Poor Water Quality"
          message: "Water quality at Rothesay Bay is {{ states('sensor.safeswim_rothesay_bay_water_quality') }}"
```

### Check if conditions are good for swimming

```yaml
template:
  - binary_sensor:
      - name: "Good Swimming Conditions"
        state: >
          {{
            states('sensor.safeswim_rothesay_bay_water_quality') == 'GREEN'
            and states('sensor.safeswim_rothesay_bay_wind_speed') | int < 20
            and states('sensor.safeswim_rothesay_bay_weather') == 'Sunny'
          }}
```

### UV protection reminder

```yaml
automation:
  - alias: "UV protection reminder"
    trigger:
      - platform: numeric_state
        entity_id: sensor.safeswim_rothesay_bay_uv_index
        above: 6
    condition:
      - condition: time
        after: "09:00:00"
        before: "17:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "☀️ High UV Level"
          message: >
            UV index is {{ states('sensor.safeswim_rothesay_bay_uv_index') }}.
            {{ state_attr('sensor.safeswim_rothesay_bay_uv_index', 'protection_recommendation') }}
```

### Alert when swimming conditions will be good tomorrow morning

```yaml
automation:
  - alias: "Good swimming forecast for tomorrow"
    trigger:
      - platform: time
        at: "19:00:00"  # Check at 7 PM each evening
    condition:
      # Check forecast for 8-10 AM tomorrow (13-15 hours from 7 PM)
      - condition: template
        value_template: >
          {% set water_quality = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h') %}
          {% set wind_speed = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h') %}
          {% set weather = state_attr('sensor.safeswim_rothesay_bay_weather', 'forecast_24h') %}
          {{
            water_quality[13:16] | select('eq', 'GREEN') | list | length == 3
            and wind_speed[13:16] | map('int') | max < 15
            and weather[13:16] | select('eq', 'Sunny') | list | length >= 2
          }}
    action:
      - service: notify.mobile_app
        data:
          title: "🏊 Great Swimming Tomorrow!"
          message: >
            Perfect beach conditions forecast for tomorrow morning (8-10 AM).
            Water quality: GREEN, winds light, mostly sunny.

### Tide-based activity planning

```yaml
automation:
  - alias: "Low tide beach walk notification"
    trigger:
      - platform: state
        entity_id: sensor.safeswim_rothesay_bay_next_low_tide
    condition:
      # Only notify if low tide is within next 2-4 hours
      - condition: template
        value_template: >
          {% set tide_time = states('sensor.safeswim_rothesay_bay_next_low_tide') | as_datetime %}
          {% set hours_away = (tide_time - now()).total_seconds() / 3600 %}
          {{ 2 <= hours_away <= 4 }}
    action:
      - service: notify.mobile_app
        data:
          title: "🌊 Low Tide Soon"
          message: >
            Low tide at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_low_tide')) | timestamp_custom('%I:%M %p') }}
            ({{ state_attr('sensor.safeswim_rothesay_bay_next_low_tide', 'height') }}m).
            Perfect time for a beach walk!

### Check forecast for specific wind direction

```yaml
automation:
  - alias: "Alert on offshore wind forecast"
    trigger:
      - platform: time_pattern
        hours: "/3"  # Check every 3 hours
    condition:
      # Check next 6 hours for offshore winds (E to SE: 45-135 degrees)
      - condition: template
        value_template: >
          {% set wind_forecast = state_attr('sensor.safeswim_rothesay_bay_wind_direction', 'forecast_24h') %}
          {% set offshore_count = wind_forecast[:6] 
            | selectattr('degrees', 'ge', 45)
            | selectattr('degrees', 'le', 135)
            | list | length %}
          {{ offshore_count >= 4 }}
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Offshore Wind Warning"
          message: >
            Offshore winds forecast for next 6 hours. Be cautious with inflatables
            and ensure children stay close to shore.

### Weekend beach day planner

```yaml
automation:
  - alias: "Weekend beach conditions summary"
    trigger:
      - platform: time
        at: "18:00:00"
      - platform: state
        entity_id: sensor.date
        to: "Friday"
    condition:
      - condition: time
        weekday:
          - fri
    action:
      - service: notify.mobile_app
        data:
          title: "🏖️ Weekend Beach Forecast"
          message: >
            Saturday forecast (10 AM-2 PM):
            Water Quality: {{ state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[16] }}
            Temp: {{ state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[16] }}°C
            Wind: {{ state_attr('sensor.safeswim_rothesay_bay_wind_direction', 'forecast_24h')[16]['direction'] }} 
            {{ state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[16] }} km/h
            UV: {{ state_attr('sensor.safeswim_rothesay_bay_uv_index', 'forecast_24h')[16] }}

### High tide kayaking conditions

```yaml
automation:
  - alias: "Good high tide kayaking conditions"
    trigger:
      - platform: state
        entity_id: sensor.safeswim_rothesay_bay_next_high_tide
    condition:
      - condition: template
        value_template: >
          {% set tide_height = state_attr('sensor.safeswim_rothesay_bay_next_high_tide', 'height') %}
          {% set tide_time = states('sensor.safeswim_rothesay_bay_next_high_tide') | as_datetime %}
          {% set hours_away = (tide_time - now()).total_seconds() / 3600 %}
          {% set hour_index = hours_away | round(0) | int %}
          {% set wind_speed = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[hour_index] %}
          {{
            tide_height > 2.5
            and 1 <= hours_away <= 3
            and wind_speed < 15
          }}
    action:
      - service: notify.mobile_app
        data:
          title: "🛶 Great Kayaking Conditions"
          message: >
            High tide ({{ state_attr('sensor.safeswim_rothesay_bay_next_high_tide', 'height') }}m) 
            at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_high_tide')) | timestamp_custom('%I:%M %p') }}
            with light winds. Perfect for kayaking!
```

## Troubleshooting

### Integration not appearing

1. Check that all files are in `/config/custom_components/safeswim/`
2. Verify `manifest.json` is valid JSON
3. Restart Home Assistant
4. Check logs: **Settings** → **System** → **Logs** (search for "safeswim")

### No locations in dropdown

- Check internet connectivity from your Home Assistant instance
- Verify Safe Swim API is accessible: `curl https://safeswim.org.nz/api/locations`
- Check Home Assistant logs for API errors

### Sensors showing "Unavailable"

- Check coordinator logs for API errors
- Verify the location still exists in the Safe Swim database
- Some locations may not have all forecast types (some may lack tide data)
- Check internet connectivity

### Entities not updating

- Default update interval is 30 minutes
- Check **Developer Tools** → **States** for last update time
- Check logs for coordinator update errors

## Development

### Testing the API

```bash
# List all locations
curl -s https://safeswim.org.nz/api/locations | jq '.locations[] | {name, slug}'

# Get forecast for specific location
curl -s https://safeswim.org.nz/api/locations/rothesay-bay | jq '.'
```

### Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.safeswim: debug
```

## Data Source

All data is provided by [Safe Swim](https://safeswim.org.nz/), a water quality monitoring service operated by Auckland Council and other regional councils in New Zealand.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/yourusername/ha-safeswim/issues).

## Changelog

### Version 1.0.0 (Initial Release)

- Support for 200+ New Zealand beach locations
- 11 sensor types per location
- Water quality monitoring with 5 status levels
- Temperature, tide, UV, weather, and wind data
- 24-hour forecasts in sensor attributes
- Dynamic icons based on conditions
- Config flow for easy setup
- Reconfigure support
- Full Home Assistant device registry integration
