#!/usr/bin/env python3
"""Test to determine what timezone the Safe Swim API uses."""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta

API_BASE = "https://safeswim.org.nz/api"

# NZ timezone offset (NZDT is UTC+13 during daylight saving, NZST is UTC+12)
# Currently it should be NZDT (summer in NZ)
NZ_OFFSET = timedelta(hours=13)


async def check_api_timezone():
    """Analyze API data to determine timezone."""
    
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE}/locations/rothesay-bay"
        
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                print(f"❌ API returned status {response.status}")
                return
            
            data = await response.json()
            forecasts = data.get("forecasts", {})
            
            print("=" * 70)
            print("TIMEZONE ANALYSIS")
            print("=" * 70)
            
            # Get current times in different timezones
            utc_now = datetime.now(timezone.utc)
            nz_now = utc_now + NZ_OFFSET
            
            print(f"\n📅 Current Times:")
            print(f"   UTC:        {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"   NZ Time:    {nz_now.strftime('%Y-%m-%d %H:%M:%S')} NZDT (UTC+13)")
            print(f"   Offset:     +13:00")
            
            # Analyze temperature data as a proxy for "current" conditions
            if "WATER_TEMPERATURE" in forecasts:
                temps = forecasts["WATER_TEMPERATURE"]
                print(f"\n🌡️ Water Temperature Forecast (first 6 hours):")
                print(f"   {temps[:6]}")
                
            if "ATMOSPHERIC_TEMPERATURE" in forecasts:
                air_temps = forecasts["ATMOSPHERIC_TEMPERATURE"]
                print(f"\n🌡️ Air Temperature Forecast (first 6 hours):")
                print(f"   {air_temps[:6]}")
                
                # Air temp typically varies more - can we infer time of day?
                print(f"\n📊 Air Temperature Pattern Analysis:")
                print(f"   Current (index 0): {air_temps[0]}°C")
                print(f"   +1 hour (index 1): {air_temps[1]}°C")
                print(f"   +2 hours (index 2): {air_temps[2]}°C")
                print(f"   +3 hours (index 3): {air_temps[3]}°C")
                
                # Check if temps are rising or falling (morning vs evening)
                if float(air_temps[0]) > float(air_temps[3]):
                    print(f"   Pattern: FALLING (suggests evening/night)")
                else:
                    print(f"   Pattern: RISING (suggests morning)")
                    
                print(f"\n   Current local NZ hour: {nz_now.hour}")
                print(f"   Current UTC hour: {utc_now.hour}")
                
            # Analyze tide data for timing clues
            if "TIDE" in forecasts:
                tide_values = forecasts["TIDE"]
                print(f"\n🌊 Tide Events:")
                
                for idx, val in enumerate(tide_values[:24]):
                    if val and val != "null":
                        # Calculate time using UTC assumption
                        utc_time = utc_now.hour + idx
                        # Calculate time using NZ assumption  
                        nz_time = nz_now.hour + idx
                        
                        print(f"   Index {idx:2d}: {val:8s} → ")
                        print(f"      If UTC: {utc_time % 24:02d}:XX UTC")
                        print(f"      If NZ:  {nz_time % 24:02d}:XX NZDT")
                        
            print("\n" + "=" * 70)
            print("INTERPRETATION")
            print("=" * 70)
            
            # The API provides forecast arrays where:
            # - Index 0 = "current hour"
            # - Index N = N hours from now
            # 
            # The question is: does the API use UTC or local NZ time as "now"?
            
            print(f"""
The API returns forecast arrays without explicit timestamps.
Array index represents hours offset from "now".

To determine timezone:
1. Compare current conditions (index 0) with actual current conditions
2. Temperature patterns should match expected time of day
3. Tide times can be verified against known tide tables

Current local time: {nz_now.strftime('%I:%M %p')}
Expected pattern: {"Evening (temps falling)" if nz_now.hour >= 18 else "Morning/Afternoon (temps rising/high)"}

Based on air temperature pattern and local time, the API likely uses:
""")
            
            # Check if pattern matches
            air_temps = forecasts.get("ATMOSPHERIC_TEMPERATURE", [])
            if len(air_temps) >= 4:
                trend = "FALLING" if float(air_temps[0]) > float(air_temps[3]) else "RISING"
                nz_hour = nz_now.hour
                
                # Evening in NZ (6 PM - midnight) should show falling temps
                # Morning in NZ (6 AM - noon) should show rising temps
                if 18 <= nz_hour <= 23 and trend == "FALLING":
                    print("   ✅ Likely NZDT - pattern matches evening temps falling")
                elif 6 <= nz_hour <= 12 and trend == "RISING":
                    print("   ✅ Likely NZDT - pattern matches morning temps rising")
                elif 12 <= nz_hour <= 18 and float(air_temps[0]) >= float(air_temps[1]):
                    print("   ✅ Likely NZDT - pattern matches afternoon temps high/plateau")
                else:
                    print("   ⚠️  Pattern unclear - need more analysis")
                    print(f"      (NZ time is {nz_now.strftime('%I:%M %p')}, trend is {trend})")


if __name__ == "__main__":
    asyncio.run(check_api_timezone())
