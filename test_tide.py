#!/usr/bin/env python3
"""Test script for improved tide functionality."""

import asyncio
import aiohttp
from datetime import datetime, timezone


API_BASE_URL = "https://safeswim.org.nz/api"


async def test_tide_improvements():
    """Test the improved tide analysis."""
    print("🌊 Testing Improved Tide Functionality\n")
    
    async with aiohttp.ClientSession() as session:
        # Fetch Rothesay Bay data
        async with session.get(f"{API_BASE_URL}/locations/rothesay-bay") as response:
            data = await response.json()
        
        forecasts = data.get("forecasts", {})
        tide_data = forecasts.get("TIDE", [])
        
        print(f"1️⃣  Raw tide data from API:")
        print(f"   Total values: {len(tide_data)}")
        non_null = [i for i, v in enumerate(tide_data) if v is not None]
        print(f"   Non-null values at indices: {non_null[:10]}...\n")
        
        print(f"2️⃣  Parsing tide events:")
        now = datetime.now(timezone.utc)
        tide_events = []
        
        for idx, tide_str in enumerate(tide_data):
            if tide_str:
                parts = tide_str.split(":")
                if len(parts) == 2:
                    height = float(parts[0])
                    minutes = int(parts[1])
                    tide_time = now.replace(second=0, microsecond=0)
                    tide_time = tide_time.replace(hour=(tide_time.hour + idx) % 24)
                    tide_time = tide_time.replace(minute=minutes)
                    
                    tide_events.append({
                        "index": idx,
                        "height": height,
                        "minutes": minutes,
                        "time": tide_time,
                    })
        
        print(f"   Found {len(tide_events)} tide events:")
        for i, event in enumerate(tide_events[:8]):
            tide_type = "HIGH" if event["height"] > 1.5 else "LOW"
            print(f"   {i+1}. {tide_type:4s} tide at +{event['index']:2d}h: {event['height']:.2f}m at :{event['minutes']:02d}")
        print()
        
        print(f"3️⃣  Determining tide direction:")
        # Find current position
        prev_event = None
        next_event = None
        
        for event in tide_events:
            if event["index"] == 0:
                # This is current hour
                continue
            if event["index"] > 0:
                if prev_event is None or event["index"] < next_event["index"] if next_event else True:
                    if event["index"] > 0:
                        next_event = event
                        break
        
        # Check what's before
        for event in reversed(tide_events):
            if event["index"] <= 0:
                prev_event = event
                break
        
        if next_event:
            if prev_event:
                direction = "RISING" if next_event["height"] > prev_event["height"] else "FALLING"
            else:
                direction = "RISING" if next_event["height"] > 1.5 else "FALLING"
            
            print(f"   Current direction: {direction}")
            if prev_event:
                print(f"   Previous event: {prev_event['height']:.2f}m at index {prev_event['index']}")
            print(f"   Next event: {next_event['height']:.2f}m at index {next_event['index']}")
        else:
            print(f"   ⚠️  Unable to determine direction (no future events)")
        print()
        
        print(f"4️⃣  Finding next high and low tides:")
        next_high = None
        next_low = None
        
        for event in tide_events:
            if event["index"] > 0:
                if event["height"] > 1.5 and next_high is None:
                    next_high = event
                elif event["height"] <= 1.5 and next_low is None:
                    next_low = event
                
                if next_high and next_low:
                    break
        
        if next_high:
            hours = next_high["index"] + (next_high["minutes"] / 60)
            print(f"   ✅ Next HIGH tide: {next_high['height']:.2f}m in {hours:.1f} hours")
        else:
            print(f"   ⚠️  No high tide found in forecast")
        
        if next_low:
            hours = next_low["index"] + (next_low["minutes"] / 60)
            print(f"   ✅ Next LOW tide: {next_low['height']:.2f}m in {hours:.1f} hours")
        else:
            print(f"   ⚠️  No low tide found in forecast")
        print()
        
        print("✅ Tide analysis complete!")
        return True


if __name__ == "__main__":
    try:
        asyncio.run(test_tide_improvements())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
