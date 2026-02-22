# Safe Swim - Automation Examples

This guide shows practical automation examples using Safe Swim forecast data. All examples use `rothesay-bay` - replace with your location slug.

## Understanding Forecast Data

### Forecast Array Structure

Each sensor provides a 24-hour `forecast_24h` attribute containing hourly values:
- **Index 0** = Current hour
- **Index 6** = 6 hours from now
- **Index 12** = 12 hours from now
- **Index 24** = 24 hours from now (if available)

### Calculating Time Offsets

To check specific times in the future, calculate the hour offset from the current time:

```python
# If it's currently 8 PM (20:00) and you want to check 8 AM tomorrow:
# 8 AM tomorrow = 12 hours ahead
forecast_index = 12

# If it's currently 7 AM (07:00) and you want to check 2 PM today:
# 2 PM today = 7 hours ahead
forecast_index = 7
```

## Beach Activity Automations

### Morning Swim Conditions Check

Get notified each evening if tomorrow morning will have good swimming conditions:

```yaml
automation:
  - alias: "Tomorrow Morning Beach Check"
    description: "Check if beach conditions will be good tomorrow morning"
    trigger:
      - platform: time
        at: "19:00:00"  # Check at 7 PM
    condition:
      # Check 8-10 AM tomorrow (13-15 hours from 7 PM)
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
            Perfect beach conditions forecast for tomorrow morning (8-10 AM):
            - Water quality: GREEN
            - Light winds (< 15 km/h)
            - Mostly sunny
            Water temp: {{ state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[14] }}°C
```

### Weekend Beach Day Planner

Get a comprehensive forecast summary on Friday evening for Saturday's beach plans:

```yaml
automation:
  - alias: "Weekend Beach Forecast Summary"
    description: "Friday evening forecast for Saturday beach day"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: time
        weekday:
          - fri
    action:
      - service: notify.mobile_app
        data:
          title: "🏖️ Weekend Beach Forecast"
          message: >
            **Saturday 10 AM - 2 PM Forecast:**
            
            Water Quality: {{ state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[16] }}
            Water Temp: {{ state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[16] }}°C
            Weather: {{ state_attr('sensor.safeswim_rothesay_bay_weather', 'forecast_24h')[16] }}
            Wind: {{ state_attr('sensor.safeswim_rothesay_bay_wind_direction', 'forecast_24h')[16]['direction'] }} 
            {{ state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[16] }} km/h
            UV Index: {{ state_attr('sensor.safeswim_rothesay_bay_uv_index', 'forecast_24h')[16] }}
            
            High Tide: {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_high_tide')) | timestamp_custom('%I:%M %p') }}
            ({{ state_attr('sensor.safeswim_rothesay_bay_next_high_tide', 'height') }}m)
```

## Tide-Based Automations

### Low Tide Rock Pool Exploration

Get notified when low tide is approaching (perfect for exploring rock pools):

```yaml
automation:
  - alias: "Low Tide Alert for Rock Pools"
    description: "Notify when low tide is 2-4 hours away"
    trigger:
      - platform: state
        entity_id: sensor.safeswim_rothesay_bay_next_low_tide
    condition:
      - condition: template
        value_template: >
          {% set tide_time = states('sensor.safeswim_rothesay_bay_next_low_tide') | as_datetime %}
          {% set hours_away = (tide_time - now()).total_seconds() / 3600 %}
          {{ 2 <= hours_away <= 4 }}
    action:
      - service: notify.mobile_app
        data:
          title: "🦀 Low Tide Soon!"
          message: >
            Low tide at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_low_tide')) | timestamp_custom('%I:%M %p') }}
            ({{ state_attr('sensor.safeswim_rothesay_bay_next_low_tide', 'height') }}m).
            
            Perfect time for:
            - Rock pool exploration
            - Beach walking
            - Shellfish gathering (check local regulations)

### High Tide Kayaking Conditions

Get notified when high tide coincides with good kayaking conditions:

```yaml
automation:
  - alias: "Ideal Kayaking Conditions"
    description: "High tide with calm winds"
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
          {% set wind_speed = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[hour_index] if hour_index < 24 else 0 %}
          {{
            tide_height > 2.5
            and 1 <= hours_away <= 3
            and wind_speed < 15
          }}
    action:
      - service: notify.mobile_app
        data:
          title: "🛶 Perfect Kayaking Conditions"
          message: >
            High tide at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_high_tide')) | timestamp_custom('%I:%M %p') }}
            ({{ state_attr('sensor.safeswim_rothesay_bay_next_high_tide', 'height') }}m)
            with light winds ({{ wind_speed }} km/h).
            
            Ideal conditions for kayaking or paddleboarding!

### Tide Rising Alert for Beachgoers

Warn when the tide is rising and high tide is approaching:

```yaml
automation:
  - alias: "Tide Rising Alert"
    description: "Alert when tide is rising towards high tide"
    trigger:
      - platform: state
        entity_id: sensor.safeswim_rothesay_bay_tide_direction
        to: "RISING"
    condition:
      - condition: template
        value_template: >
          {% set tide_time = states('sensor.safeswim_rothesay_bay_next_high_tide') | as_datetime %}
          {% set hours_away = (tide_time - now()).total_seconds() / 3600 %}
          {{ hours_away < 2 }}
    action:
      - service: notify.mobile_app
        data:
          title: "⬆️ Tide Rising"
          message: >
            Tide is rising. High tide at {{ as_timestamp(states('sensor.safeswim_rothesay_bay_next_high_tide')) | timestamp_custom('%I:%M %p') }}.
            Move belongings higher up the beach!
```

## Safety Automations

### Offshore Wind Warning

Alert when offshore winds are forecast (dangerous for inflatables and weak swimmers):

```yaml
automation:
  - alias: "Offshore Wind Forecast Alert"
    description: "Warn about dangerous offshore winds"
    trigger:
      - platform: time_pattern
        hours: "/3"  # Check every 3 hours
    condition:
      # Offshore winds for NZ east coast beaches: E to SE (45-135 degrees)
      # Adjust range based on your beach's orientation
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
            Offshore winds forecast for next 6 hours.
            
            Safety tips:
            - Keep children close to shore
            - Avoid using inflatables
            - Be cautious with paddleboards
            - Stay between the flags if patrolled

### Strong Wind Alert

Warn about dangerous wind conditions forecast:

```yaml
automation:
  - alias: "Strong Wind Forecast"
    description: "Alert when strong winds are forecast"
    trigger:
      - platform: time_pattern
        hours: "/6"
    condition:
      - condition: template
        value_template: >
          {% set wind_forecast = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h') %}
          {% set max_wind = wind_forecast[:12] | map('int') | max %}
          {{ max_wind > 30 }}
    action:
      - service: notify.mobile_app
        data:
          title: "💨 Strong Wind Alert"
          message: >
            Strong winds forecast in next 12 hours (up to {{ wind_forecast[:12] | map('int') | max }} km/h).
            Beach activities may be dangerous.

### Poor Water Quality Alert

Get notified when water quality deteriorates in the forecast:

```yaml
automation:
  - alias: "Water Quality Forecast Alert"
    description: "Alert when poor water quality is forecast"
    trigger:
      - platform: time
        at: "06:00:00"
    condition:
      - condition: template
        value_template: >
          {% set quality_forecast = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h') %}
          {% set poor_quality = quality_forecast[:12] 
            | reject('eq', 'GREEN') 
            | reject('eq', 'GREY')
            | list | length %}
          {{ poor_quality > 0 }}
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Poor Water Quality Forecast"
          message: >
            Poor water quality forecast for today.
            Consider visiting a different beach.
```

## UV Protection Automations

### Morning UV Alert

Get notified in the morning if high UV is forecast for the day:

```yaml
automation:
  - alias: "High UV Forecast"
    description: "Morning alert for high UV day"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: template
        value_template: >
          {% set uv_forecast = state_attr('sensor.safeswim_rothesay_bay_uv_index', 'forecast_24h') %}
          {% set max_uv = uv_forecast[0:12] | map('int') | max %}
          {{ max_uv >= 6 }}
    action:
      - service: notify.mobile_app
        data:
          title: "☀️ High UV Forecast Today"
          message: >
            Peak UV index: {{ uv_forecast[0:12] | map('int') | max }}
            
            Protection needed:
            - Wear sunscreen (SPF 30+)
            - Seek shade 10 AM - 4 PM
            - Wear protective clothing
            - Use sunglasses

### UV Peak Time Reminder

Remind to reapply sunscreen during peak UV hours:

```yaml
automation:
  - alias: "Sunscreen Reminder"
    description: "Remind to reapply sunscreen during high UV"
    trigger:
      - platform: time
        at:
          - "11:00:00"
          - "13:00:00"
          - "15:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.safeswim_rothesay_bay_uv_index
        above: 5
    action:
      - service: notify.mobile_app
        data:
          title: "🧴 Sunscreen Reminder"
          message: >
            UV index is {{ states('sensor.safeswim_rothesay_bay_uv_index') }}.
            Time to reapply sunscreen!
```

## Advanced Template Sensors

### Overall Beach Conditions Score

Create a sensor that scores beach conditions:

```yaml
template:
  - sensor:
      - name: "Beach Conditions Score"
        unique_id: beach_conditions_score
        state: >
          {% set score = 0 %}
          
          {# Water quality (30 points) #}
          {% set wq = states('sensor.safeswim_rothesay_bay_water_quality') %}
          {% if wq == 'GREEN' %}{% set score = score + 30 %}
          {% elif wq == 'GREY' %}{% set score = score + 15 %}{% endif %}
          
          {# Wind speed (25 points) #}
          {% set wind = states('sensor.safeswim_rothesay_bay_wind_speed') | int(0) %}
          {% if wind < 10 %}{% set score = score + 25 %}
          {% elif wind < 20 %}{% set score = score + 15 %}
          {% elif wind < 30 %}{% set score = score + 5 %}{% endif %}
          
          {# Weather (20 points) #}
          {% if states('sensor.safeswim_rothesay_bay_weather') == 'Sunny' %}
            {% set score = score + 20 %}
          {% else %}
            {% set score = score + 10 %}
          {% endif %}
          
          {# UV index (15 points) - moderate is good #}
          {% set uv = states('sensor.safeswim_rothesay_bay_uv_index') | int(0) %}
          {% if 2 <= uv <= 7 %}{% set score = score + 15 %}
          {% elif uv < 2 or uv > 10 %}{% set score = score + 5 %}
          {% else %}{% set score = score + 10 %}{% endif %}
          
          {# Water temperature (10 points) #}
          {% set temp = states('sensor.safeswim_rothesay_bay_water_temperature') | float(0) %}
          {% if temp >= 20 %}{% set score = score + 10 %}
          {% elif temp >= 18 %}{% set score = score + 7 %}
          {% elif temp >= 15 %}{% set score = score + 4 %}{% endif %}
          
          {{ score }}
        attributes:
          rating: >
            {% set score = states('sensor.beach_conditions_score') | int(0) %}
            {% if score >= 80 %}Excellent
            {% elif score >= 60 %}Good
            {% elif score >= 40 %}Fair
            {% elif score >= 20 %}Poor
            {% else %}Very Poor{% endif %}
          water_quality: "{{ states('sensor.safeswim_rothesay_bay_water_quality') }}"
          wind_speed: "{{ states('sensor.safeswim_rothesay_bay_wind_speed') }} km/h"
          weather: "{{ states('sensor.safeswim_rothesay_bay_weather') }}"
          uv_index: "{{ states('sensor.safeswim_rothesay_bay_uv_index') }}"
          water_temp: "{{ states('sensor.safeswim_rothesay_bay_water_temperature') }}°C"

### Next 6 Hours Beach Status

Create a sensor showing conditions for the next 6 hours:

```yaml
template:
  - sensor:
      - name: "Next 6 Hours Beach Forecast"
        unique_id: next_6h_beach_forecast
        state: >
          {% set wq = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[:6] %}
          {% if wq | select('in', ['RED', 'RED+', 'BLACK']) | list | length > 0 %}
            Poor Quality Forecast
          {% elif wq | select('eq', 'GREEN') | list | length >= 5 %}
            Excellent
          {% else %}
            Good
          {% endif %}
        attributes:
          water_quality: >
            {{ state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[:6] }}
          water_temp_range: >
            {% set temps = state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[:6] | map('float') %}
            {{ temps | min | round(1) }}-{{ temps | max | round(1) }}°C
          wind_range: >
            {% set winds = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[:6] | map('int') %}
            {{ winds | min }}-{{ winds | max }} km/h
          weather_summary: >
            {% set weather = state_attr('sensor.safeswim_rothesay_bay_weather', 'forecast_24h')[:6] %}
            {% set sunny = weather | select('eq', 'Sunny') | list | length %}
            {{ sunny }}/6 hours sunny
```

## Dashboard Cards

### Forecast Chart Card (ApexCharts)

Requires: [ApexCharts Card](https://github.com/RomRider/apexcharts-card)

```yaml
type: custom:apexcharts-card
header:
  title: 24-Hour Beach Forecast
  show: true
series:
  - entity: sensor.safeswim_rothesay_bay_water_temperature
    data_generator: |
      return entity.attributes.forecast_24h.map((temp, index) => {
        return [new Date().getTime() + (index * 3600000), temp];
      });
    name: Water Temp
    stroke_width: 2
  
  - entity: sensor.safeswim_rothesay_bay_air_temperature
    data_generator: |
      return entity.attributes.forecast_24h.map((temp, index) => {
        return [new Date().getTime() + (index * 3600000), temp];
      });
    name: Air Temp
    stroke_width: 2
```

### Conditions Summary Card

```yaml
type: markdown
content: >
  ## Beach Conditions
  
  **Current:** {{ states('sensor.safeswim_rothesay_bay_water_quality') }}
  
  **Temp:** {{ states('sensor.safeswim_rothesay_bay_water_temperature') }}°C
  
  **Wind:** {{ states('sensor.safeswim_rothesay_bay_wind_direction') }} 
  {{ states('sensor.safeswim_rothesay_bay_wind_speed') }} km/h
  
  **Tide:** {{ states('sensor.safeswim_rothesay_bay_tide_direction') }}
  
  ---
  
  **Next 6 Hours:**
  {% set wq = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h')[:6] %}
  {% set temp = state_attr('sensor.safeswim_rothesay_bay_water_temperature', 'forecast_24h')[:6] %}
  {% set wind = state_attr('sensor.safeswim_rothesay_bay_wind_speed', 'forecast_24h')[:6] %}
  
  Quality: {{ wq | join(' → ') }}
  
  Temp: {{ temp | map('round', 1) | join('° → ') }}°C
  
  Wind: {{ wind | map('int') | join(' → ') }} km/h

## Tips & Tricks

### Testing Automations

Use the **Developer Tools → Template** tab to test your templates before using them in automations:

```yaml
{% set forecast = state_attr('sensor.safeswim_rothesay_bay_water_quality', 'forecast_24h') %}
{{ forecast[:6] }}
```

### Time Zone Considerations

**The Safe Swim API uses New Zealand local time (Pacific/Auckland), NOT UTC.** 

**How this was determined:**
1. Tested API at 8:34 PM NZ time / 7:34 AM UTC
2. Air temperature forecast showed FALLING pattern (18.7°C → 15.9°C)
3. Falling temperatures indicate evening, confirming API uses NZ time (not UTC morning)
4. Created test script (`test_timezone.py`) that analyzes temperature patterns vs. time of day

**Impact on integration:**
- Forecast array index 0 = current hour in NZ time
- Tide timestamps are in Pacific/Auckland timezone
- Home Assistant automatically converts all timestamps to your configured timezone for display

**For developers:** The integration correctly uses `ZoneInfo("Pacific/Auckland")` for all datetime calculations.

### Forecast Accuracy

- Forecasts are updated every 30 minutes
- Weather/temperature forecasts are generally reliable 12-24 hours ahead
- Tide predictions are highly accurate (based on astronomical calculations)
- Water quality can change rapidly due to rainfall or other factors

### Customization

Replace `rothesay-bay` with your location slug in all examples. Find your location slug by looking at the entity IDs created when you set up the integration.
