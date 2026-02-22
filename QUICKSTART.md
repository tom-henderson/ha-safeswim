# Safe Swim - Quick Start Guide

## 🚀 Installation (5 Minutes)

### Step 1: Copy Files
```bash
# From your download/development folder
cp -r custom_components/safeswim /config/custom_components/

# Or if using SSH to Home Assistant
scp -r custom_components/safeswim root@homeassistant.local:/config/custom_components/
```

### Step 2: Restart Home Assistant
```bash
# Home Assistant OS
ha core restart

# Docker
docker restart homeassistant

# Or via UI: Settings → System → Restart
```

### Step 3: Add Integration
1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **"Safe Swim"**
4. Select your beach from the dropdown
5. Done! ✅

## 📊 What You Get

Each location creates **11 sensors**:

| Sensor | What It Shows | Example |
|--------|--------------|---------|
| 🌊 Water Quality | Swimming safety | GREEN, RED, BLACK |
| 🌡️ Water Temperature | Water temp | 22.3°C |
| 🌡️ Air Temperature | Air temp | 19.2°C |
| 🌊 Tide Direction | Tide state | RISING, FALLING |
| ⬆️ Next High Tide | High tide time | Today, 10:09 AM |
| ⬇️ Next Low Tide | Low tide time | Today, 4:00 PM |
| ☀️ UV Index | Sun strength | 6 (High) |
| 🌤️ Weather | Conditions | Sunny, Cloudy |
| 🧭 Wind Direction | Wind direction | WSW |
| 💨 Wind Speed | Wind speed | 12 km/h |
| ℹ️ Location Info | Beach details | Facilities, Hazards |

## 🎯 Quick Use Cases

### Dashboard Card
Add to your Lovelace dashboard:
```yaml
type: entities
title: Rothesay Bay
entities:
  - sensor.safeswim_rothesay_bay_water_quality
  - sensor.safeswim_rothesay_bay_water_temperature
  - sensor.safeswim_rothesay_bay_weather
  - sensor.safeswim_rothesay_bay_uv_index
```

### Simple Automation
Get notified when water quality is poor:
```yaml
automation:
  - alias: "Poor Water Quality Alert"
    trigger:
      platform: state
      entity_id: sensor.safeswim_rothesay_bay_water_quality
      to:
        - RED
        - BLACK
    action:
      service: notify.mobile_app
      data:
        message: "⚠️ Water quality is poor at Rothesay Bay"
```

### Swimming Conditions Template
```yaml
template:
  - binary_sensor:
      - name: "Good for Swimming"
        state: >
          {{
            states('sensor.safeswim_rothesay_bay_water_quality') == 'GREEN'
            and states('sensor.safeswim_rothesay_bay_wind_speed')|int < 20
          }}
```

### Check Tomorrow's Morning Conditions
```yaml
automation:
  - alias: "Tomorrow Morning Beach Check"
    trigger:
      platform: time
      at: "20:00:00"
    condition:
      # Check 8-10 AM tomorrow (12-14 hours ahead from 8 PM)
      - condition: template
        value_template: >
          {% set forecast = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h') %}
          {{ forecast[12:15] | select('eq', 'GREEN') | list | length == 3 }}
    action:
      service: notify.mobile_app
      data:
        message: "🏊 Perfect beach conditions forecast for tomorrow morning!"
```

### Tide Alert for Beach Activities
```yaml
automation:
  - alias: "Low Tide Beach Walk"
    trigger:
      platform: state
      entity_id: sensor.safeswim_rothesay_bay_next_low_tide
    action:
      service: notify.mobile_app
      data:
        message: >
          Low tide at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_low_tide')) | timestamp_custom('%I:%M %p') }}.
          Great time for exploring rock pools!
```

## 🏖️ Popular Locations

**Auckland Beaches:**
- Mission Bay: `mission-bay`
- Takapuna Beach: `takapuna-beach`
- Browns Bay: `browns-bay`
- Rothesay Bay: `rothesay-bay`
- Long Bay: `long-bay`
- Piha Beach: `piha-beach`

**Other Regions:**
- Search in the dropdown - 315+ locations available!

## 🔧 Configuration

### Add Another Location
Just add the integration again with a different location!

### Change Location
1. Go to **Settings** → **Devices & Services** → **Safe Swim**
2. Click on the location device
3. Click **Configure**
4. Select new location

### Enable Location Info Sensor
(Disabled by default - shows facilities, hazards, etc.)
1. Go to **Settings** → **Devices & Services** → **Safe Swim**
2. Click on the location device
3. Click the disabled **Location Info** entity
4. Click **Enable**

## 📱 Example Dashboard

```yaml
type: grid
cards:
  - type: entity
    entity: sensor.safeswim_rothesay_bay_water_quality
    name: Water Quality
    icon: mdi:water
  
  - type: entity
    entity: sensor.safeswim_rothesay_bay_water_temperature
    name: Water Temp
  
  - type: entity
    entity: sensor.safeswim_rothesay_bay_uv_index
    name: UV Index
  
  - type: entity
    entity: sensor.safeswim_rothesay_bay_wind_speed
    name: Wind

  - type: markdown
    content: >
      **Next 6 Hours:**
      
      {% set wq = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[:6] %}
      {% set temp = state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[:6] %}
      {% set wind = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[:6] %}
      
      Quality: {{ wq | join(', ') }}
      
      Temp: {{ temp | join('°C, ') }}°C
      
      Wind: {{ wind | join(', ') }} km/h
  
  - type: entities
    title: Tides
    entities:
      - entity: sensor.safeswim_rothesay_bay_tide_direction
      - entity: sensor.safeswim_rothesay_bay_next_high_tide
      - entity: sensor.safeswim_rothesay_bay_next_low_tide
```

## 📊 Accessing Forecast Data

Each sensor includes 24-hour forecast data in its attributes:

```yaml
# In templates or automations:
{{ state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h') }}
# Returns: ['GREEN', 'GREEN', 'GREEN', ...]

# Get specific hour (e.g., 3 hours from now):
{{ state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[3] }}
# Returns: 22.1

# Check range (e.g., tomorrow morning 8-11 AM from 8 PM):
{{ state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[12:16] }}
# Returns: ['GREEN', 'GREEN', 'GREEN', 'GREEN']

# Wind forecast with direction:
{{ state_attr('sensor.safeswim_rothesay_bay_wind_direction', 'forecast_24h')[0] }}
# Returns: {'degrees': 236, 'direction': 'WSW'}
```

## ❓ Troubleshooting

**Integration not showing up?**
- Check files are in `/config/custom_components/safeswim/`
- Restart Home Assistant
- Check logs: Settings → System → Logs

**Sensors show "Unavailable"?**
- Check internet connection
- Wait 30 minutes (default update interval)
- Check logs for API errors

**Need help?**
- Check [README.md](README.md) for detailed docs
- Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for technical details
- Run `python3 test_api.py` to test API connectivity

## 🎨 Icon Colors

Water Quality icons change color by state:
- 🟢 **GREEN**: Safe to swim
- ⚪ **GREY**: Uncertain
- 🟠 **RED**: Not advised
- 🔴 **BLACK**: Do not swim

## ⏱️ Update Frequency

Data updates every **30 minutes** automatically. No action needed!

## 🌐 Data Source

All data from [Safe Swim](https://safeswim.org.nz/) - Auckland Council's water quality monitoring service.

---

**That's it! You're ready to monitor your favorite beach! 🏖️**
