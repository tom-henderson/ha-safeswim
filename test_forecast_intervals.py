#!/usr/bin/env python3
"""Test and validate forecast data intervals from Safe Swim API."""

import asyncio
import aiohttp
from datetime import datetime

API_BASE = "https://safeswim.org.nz/api"


async def analyze_forecast_structure():
    """Fetch forecast data and analyze its structure."""
    
    async with aiohttp.ClientSession() as session:
        # Get a location forecast (using Rothesay Bay as example)
        url = f"{API_BASE}/locations/rothesay-bay"
        
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                print(f"❌ API returned status {response.status}")
                return
            
            data = await response.json()
            
            print("=" * 70)
            print("API RESPONSE STRUCTURE")
            print("=" * 70)
            print(f"Top-level keys: {list(data.keys())}")
            
            # Print a sample of the raw data to understand structure
            import json
            print("\nFirst 1000 chars of response:")
            print(json.dumps(data, indent=2)[:1000])
            print()
            
            forecasts = data.get("forecasts", {})
            
            print("=" * 70)
            print("FORECAST DATA STRUCTURE ANALYSIS")
            print("=" * 70)
            print(f"Location: {data.get('name')}")
            print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Forecast keys: {list(forecasts.keys()) if forecasts else 'NO FORECAST KEY'}")
            print()
            
            # Analyze each forecast type
            forecast_types = [
                "WATER_QUALITY",
                "WATER_TEMPERATURE",
                "ATMOSPHERIC_TEMPERATURE",
                "TIDE",
                "UV_INDEX",
                "WEATHER_CONDITIONS",
                "WIND_DIRECTION",
                "WIND_SPEED",
            ]
            
            for forecast_type in forecast_types:
                if forecast_type not in forecasts:
                    print(f"⚠️  {forecast_type}: NOT PRESENT")
                    continue
                
                values = forecasts[forecast_type]
                non_null_count = sum(1 for v in values if v is not None and v != "" and v != "null")
                null_count = len(values) - non_null_count
                
                print(f"\n📊 {forecast_type}:")
                print(f"   Total values: {len(values)}")
                print(f"   Non-null: {non_null_count}")
                print(f"   Null/empty: {null_count}")
                
                # Show first 25 values with their indices
                print(f"   First 25 values (index: value):")
                for i in range(min(25, len(values))):
                    value = values[i]
                    if value is None or value == "" or value == "null":
                        display = "NULL"
                    else:
                        display = str(value)[:20]  # Truncate long values
                    print(f"      [{i:2d}]: {display}")
                
                # Find patterns in null values
                if null_count > 0:
                    null_indices = [i for i, v in enumerate(values) if v is None or v == "" or v == "null"]
                    print(f"   Null value indices: {null_indices[:20]}{'...' if len(null_indices) > 20 else ''}")
                    
                    # Check for patterns (e.g., every other, specific hours)
                    if len(null_indices) > 1:
                        gaps = [null_indices[i+1] - null_indices[i] for i in range(len(null_indices)-1)]
                        if gaps:
                            unique_gaps = set(gaps)
                            if len(unique_gaps) == 1:
                                print(f"   Pattern: Nulls occur every {list(unique_gaps)[0]} positions")
                            else:
                                print(f"   Gap pattern: {unique_gaps}")
            
            print("\n" + "=" * 70)
            print("ANALYSIS SUMMARY")
            print("=" * 70)
            
            # Check if all forecasts have the same length
            lengths = {k: len(v) for k, v in forecasts.items() if isinstance(v, list)}
            unique_lengths = set(lengths.values())
            
            if len(unique_lengths) == 1:
                total_length = list(unique_lengths)[0]
                print(f"✅ All forecast arrays have the same length: {total_length}")
                print(f"   This suggests {total_length}-hour forecast window")
            else:
                print(f"⚠️  Different array lengths found: {lengths}")
            
            # Analyze tide data specifically (since it's sparse)
            if "tide" in forecasts:
                tide_values = forecasts["tide"]
                tide_events = []
                for i, val in enumerate(tide_values):
                    if val and val != "null":
                        tide_events.append((i, val))
                
                print(f"\n🌊 TIDE DATA ANALYSIS:")
                print(f"   Total tide events: {len(tide_events)}")
                if tide_events:
                    print(f"   Tide events (hour_offset: value):")
                    for idx, val in tide_events[:10]:
                        print(f"      Hour +{idx}: {val}")
                    
                    # Calculate gaps between tide events
                    if len(tide_events) > 1:
                        gaps = [tide_events[i+1][0] - tide_events[i][0] for i in range(len(tide_events)-1)]
                        avg_gap = sum(gaps) / len(gaps)
                        print(f"   Average gap between tide events: {avg_gap:.1f} hours")
                        print(f"   Gap range: {min(gaps)} to {max(gaps)} hours")


if __name__ == "__main__":
    asyncio.run(analyze_forecast_structure())
