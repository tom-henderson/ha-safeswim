# Tide Feature Improvement Plan

## Current Understanding of API Data

### ✅ Assumptions Confirmed

Based on analysis of Rothesay Bay tide data:

**Data Format**: `"height:minutes"` 
- Example: `"2.79:9"` = 2.79 meters at 9 minutes past the hour

**Data Pattern**:
```
Index | Value     | Height | Type
------|-----------|--------|------
4     | "0.34:0"  | 0.34m  | LOW
10    | "2.79:9"  | 2.79m  | HIGH
16    | "0.4:16"  | 0.4m   | LOW
22    | "2.89:28" | 2.89m  | HIGH
28    | "0.33:44" | 0.33m  | LOW
34    | "2.78:57" | 2.78m  | HIGH
```

**Key Observations**:
1. ✅ Values only appear at HIGH and LOW tide points
2. ✅ Null values pad the array (one value per hour, 72 total)
3. ✅ Array index represents hours from current time
4. ✅ Minutes value is the exact minute past the hour when tide occurs
5. ✅ Classic semi-diurnal tide pattern (~6 hours between events)
6. ✅ Alternating LOW-HIGH-LOW-HIGH pattern
7. ✅ Low tides: ~0.3-0.6m, High tides: ~2.7-3.0m

### ❌ Current Tide Calculation Not Possible

**Question**: Can we calculate current tide height between events?

**Answer**: **NO** - Insufficient data in API

**Evidence**: 
- Only have exact heights at HIGH/LOW points
- No information about:
  - Tidal curve shape (sinusoidal vs. asymmetric)
  - Tidal constituents (M2, S2, K1, etc.)
  - Local bathymetry effects
  - Phase information
  
**Conclusion**: Accurate interpolation requires harmonic analysis data not provided by API.

## Proposed Improvements

### New Entities to Add

1. **Tide Direction Sensor**
   - Entity: `sensor.safeswim_{location}_tide_direction`
   - States: `RISING`, `FALLING`, `HIGH`, `LOW`
   - Logic:
     - Find previous and next tide events
     - Compare heights to determine direction
     - Show `HIGH` when at high tide event (±15 min)
     - Show `LOW` when at low tide event (±15 min)

2. **Next High Tide Sensor**
   - Entity: `sensor.safeswim_{location}_next_high_tide`
   - State: Time until next high tide (hours)
   - Attributes:
     - `time`: Exact datetime of high tide
     - `height`: Height in meters
     - `height_formatted`: e.g., "2.79 m"

3. **Next Low Tide Sensor**
   - Entity: `sensor.safeswim_{location}_next_low_tide`
   - State: Time until next low tide (hours)
   - Attributes:
     - `time`: Exact datetime of low tide
     - `height`: Height in meters
     - `height_formatted`: e.g., "0.34 m"

### Modifications to Existing Tide Sensor

**Current**: Shows current tide height (may be None)
**Improved**: Shows "next event" information

Options:
1. Keep as-is but improve attributes
2. Change to show "status" text: "Rising toward 2.79m at 10:09"
3. Remove and replace with the 3 new sensors above

**Recommendation**: Option 3 - Replace with new sensors for clarity

## Implementation Details

### Tide Analysis Helper Functions

```python
def analyze_tide_data(forecasts: dict) -> dict:
    """Analyze tide forecast data.
    
    Returns:
        {
            'current_direction': 'RISING' | 'FALLING' | 'HIGH' | 'LOW' | None,
            'next_high': {'hours': float, 'height': float, 'time': datetime} | None,
            'next_low': {'hours': float, 'height': float, 'time': datetime} | None,
            'tide_events': [list of all events],
        }
    """
```

### Implementation Steps

1. **Create tide analysis functions** (in `sensor.py` or `tide_utils.py`)
   - `parse_tide_events()` - Extract all tide events from forecast array
   - `get_tide_direction()` - Determine if RISING/FALLING/HIGH/LOW
   - `find_next_high_tide()` - Find next high tide event
   - `find_next_low_tide()` - Find next low tide event
   - `calculate_tide_time()` - Convert index + minutes to datetime

2. **Add new sensor descriptions** to `SENSOR_TYPES`
   - Remove or modify existing tide sensor
   - Add tide_direction sensor
   - Add next_high_tide sensor
   - Add next_low_tide sensor

3. **Update constants** (`const.py`)
   - Add tide-related constants
   - Tide height thresholds (if needed)

4. **Testing**
   - Test with various locations (some may not have tide data)
   - Test edge cases (at exact tide time, etc.)
   - Verify datetime calculations are correct

## Algorithm Details

### Determining Tide Direction

```python
def get_tide_direction(tide_events: list, current_index: int = 0) -> str:
    """
    Args:
        tide_events: List of (index, height, minutes) tuples
        current_index: Current hour (0 = now, 1 = 1 hour from now, etc.)
    
    Returns:
        'RISING', 'FALLING', 'HIGH', 'LOW', or None
    """
    if not tide_events:
        return None
    
    # Find events before and after current time
    prev_event = None
    next_event = None
    
    for event in tide_events:
        if event['index'] <= current_index:
            prev_event = event
        elif event['index'] > current_index and next_event is None:
            next_event = event
            break
    
    # If at or very close to an event (within 15 minutes of that hour)
    if next_event and next_event['index'] == current_index:
        return 'HIGH' if next_event['height'] > 1.5 else 'LOW'
    
    if prev_event and prev_event['index'] == current_index:
        return 'HIGH' if prev_event['height'] > 1.5 else 'LOW'
    
    # Determine direction based on next event
    if next_event:
        if prev_event:
            # Have both - compare heights
            if next_event['height'] > prev_event['height']:
                return 'RISING'
            else:
                return 'FALLING'
        else:
            # Only have next event - check if it's high or low
            # If next is high, we must be rising; if next is low, we must be falling
            return 'RISING' if next_event['height'] > 1.5 else 'FALLING'
    
    return None
```

### Finding Next High/Low Tide

```python
def find_next_high_tide(tide_events: list, current_index: int = 0) -> dict | None:
    """Find the next high tide event after current time."""
    for event in tide_events:
        if event['index'] > current_index and event['height'] > 1.5:
            # Calculate actual datetime
            hours_from_now = event['index']
            minutes_offset = event['minutes']
            tide_time = datetime.now() + timedelta(hours=hours_from_now, minutes=minutes_offset)
            
            return {
                'hours': hours_from_now + (minutes_offset / 60),
                'height': event['height'],
                'time': tide_time,
            }
    return None

def find_next_low_tide(tide_events: list, current_index: int = 0) -> dict | None:
    """Find the next low tide event after current time."""
    for event in tide_events:
        if event['index'] > current_index and event['height'] <= 1.5:
            # Calculate actual datetime
            hours_from_now = event['index']
            minutes_offset = event['minutes']
            tide_time = datetime.now() + timedelta(hours=hours_from_now, minutes=minutes_offset)
            
            return {
                'hours': hours_from_now + (minutes_offset / 60),
                'height': event['height'],
                'time': tide_time,
            }
    return None
```

### Height Threshold Logic

Looking at the data:
- Low tides: 0.3m - 0.6m (typically)
- High tides: 2.7m - 3.0m (typically)
- **Threshold**: Use **1.5m** as cutoff
  - Below 1.5m = LOW tide
  - Above 1.5m = HIGH tide

This threshold may need adjustment for different locations/regions.

## Entity Design

### 1. Tide Direction Sensor

```python
SafeSwimSensorEntityDescription(
    key="tide_direction",
    translation_key="tide_direction",
    icon="mdi:waves-arrow-up",  # or mdi:waves-arrow-down dynamically
    value_fn=lambda data: get_tide_direction_from_data(data),
    attributes_fn=lambda data: {
        "previous_tide": {...},
        "next_tide": {...},
    },
)
```

**Icon Logic**:
- RISING: `mdi:waves-arrow-up`
- FALLING: `mdi:waves-arrow-down`
- HIGH: `mdi:waves`
- LOW: `mdi:wave`

### 2. Next High Tide Sensor

```python
SafeSwimSensorEntityDescription(
    key="next_high_tide",
    translation_key="next_high_tide",
    icon="mdi:arrow-up-bold",
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement="h",
    value_fn=lambda data: get_next_high_tide_hours(data),
    attributes_fn=lambda data: {
        "time": get_next_high_tide_time(data),
        "height": get_next_high_tide_height(data),
        "height_formatted": f"{height}m",
    },
)
```

### 3. Next Low Tide Sensor

```python
SafeSwimSensorEntityDescription(
    key="next_low_tide",
    translation_key="next_low_tide",
    icon="mdi:arrow-down-bold",
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement="h",
    value_fn=lambda data: get_next_low_tide_hours(data),
    attributes_fn=lambda data: {
        "time": get_next_low_tide_time(data),
        "height": get_next_low_tide_height(data),
        "height_formatted": f"{height}m",
    },
)
```

## Edge Cases to Handle

1. **No tide data available**: Return None / Unavailable
2. **At exact tide time**: Show HIGH or LOW state
3. **Less than 2 tide events**: May not be able to determine direction
4. **Locations without tide data**: Sensors should be unavailable
5. **Timezone considerations**: Ensure datetime calculations use correct timezone

## Migration From Current Implementation

### Option A: Remove old tide sensor
- Delete existing "tide" sensor
- Add 3 new sensors
- **Breaking change** for users

### Option B: Keep old tide sensor + add new ones
- Add 3 new sensors alongside existing
- Mark old one as deprecated in docs
- Remove in v2.0

**Recommendation**: Option A - Clean break, better UX

## Testing Plan

1. Test with Rothesay Bay (has good tide data)
2. Test with location that has no tide data
3. Test at different times of day:
   - During rising tide
   - During falling tide
   - At high tide event
   - At low tide event
4. Verify datetime calculations are accurate
5. Check timezone handling

## Updated Sensors Summary

After implementation:

| Old Sensor | New Sensors |
|------------|-------------|
| ❌ `sensor.safeswim_{location}_tide` | ✅ `sensor.safeswim_{location}_tide_direction` |
| | ✅ `sensor.safeswim_{location}_next_high_tide` |
| | ✅ `sensor.safeswim_{location}_next_low_tide` |

**Total**: 3 tide-related sensors (instead of 1)

## User Benefits

1. **Clear direction**: Know if tide is rising or falling
2. **Planning**: See when next high/low tide occurs
3. **Better UX**: Time-based sensors (can show "in 4.5 hours")
4. **Accurate data**: Not attempting impossible interpolation

## Implementation Estimate

- **Time**: 2-3 hours
- **Files to modify**: 
  - `sensor.py` (main changes)
  - `const.py` (new constants)
  - `strings.json` (new translations)
  - `translations/en.json` (new translations)
- **Testing**: 30 minutes
- **Documentation**: 30 minutes

**Total**: ~3-4 hours

---

## Decision Required

Before implementing, confirm:
1. ✅ Are you okay with removing the old tide sensor?
2. ✅ Do you want duration in hours or a timestamp?
3. ✅ Should we use 1.5m as the high/low threshold?

Once confirmed, I'll proceed with implementation.
