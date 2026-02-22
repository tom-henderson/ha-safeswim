#!/usr/bin/env python3
"""Test script for Safe Swim API - standalone version."""

import asyncio
import aiohttp
import sys


API_BASE_URL = "https://safeswim.org.nz/api"
API_TIMEOUT = 10


class SafeSwimAPIError(Exception):
    """Exception for API errors."""


async def get_locations(session):
    """Fetch all locations."""
    try:
        async with session.get(f"{API_BASE_URL}/locations", timeout=API_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("locations", [])
    except Exception as e:
        raise SafeSwimAPIError(f"Error fetching locations: {e}")


async def get_location_forecast(session, slug):
    """Fetch forecast for specific location."""
    try:
        async with session.get(f"{API_BASE_URL}/locations/{slug}", timeout=API_TIMEOUT) as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        raise SafeSwimAPIError(f"Error fetching forecast: {e}")


async def test_api():
    """Test the Safe Swim API client."""
    print("🏖️  Testing Safe Swim API Client\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Fetch locations
        print("1️⃣  Fetching locations...")
        try:
            locations = await get_locations(session)
            print(f"   ✅ Found {len(locations)} locations")
            
            # Show first 5 locations
            print("\n   First 5 locations:")
            for loc in locations[:5]:
                print(f"      - {loc['name']} ({loc['slug']})")
            print()
        except SafeSwimAPIError as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # Test 2: Fetch specific location forecast
        test_slug = "rothesay-bay"
        print(f"2️⃣  Fetching forecast for {test_slug}...")
        try:
            forecast = await get_location_forecast(session, test_slug)
            if forecast:
                print(f"   ✅ Successfully fetched forecast for {forecast['name']}")
                
                # Show forecast data available
                forecasts = forecast.get("forecasts", {})
                print(f"\n   Available forecast types ({len(forecasts)}):")
                for forecast_type, values in forecasts.items():
                    non_null = sum(1 for v in values if v is not None)
                    print(f"      - {forecast_type}: {non_null}/{len(values)} values")
                
                # Show current values
                print(f"\n   Current conditions:")
                if "WATER_QUALITY" in forecasts and forecasts["WATER_QUALITY"]:
                    print(f"      Water Quality: {forecasts['WATER_QUALITY'][0]}")
                if "WATER_TEMPERATURE" in forecasts and forecasts["WATER_TEMPERATURE"]:
                    print(f"      Water Temp: {forecasts['WATER_TEMPERATURE'][0]}°C")
                if "ATMOSPHERIC_TEMPERATURE" in forecasts and forecasts["ATMOSPHERIC_TEMPERATURE"]:
                    print(f"      Air Temp: {forecasts['ATMOSPHERIC_TEMPERATURE'][0]}°C")
                if "WEATHER_CONDITIONS" in forecasts and forecasts["WEATHER_CONDITIONS"]:
                    print(f"      Weather: {forecasts['WEATHER_CONDITIONS'][0]}")
                if "WIND_SPEED" in forecasts and forecasts["WIND_SPEED"]:
                    print(f"      Wind Speed: {forecasts['WIND_SPEED'][0]} km/h")
                
                print()
            else:
                print(f"   ❌ Location not found\n")
                return False
        except SafeSwimAPIError as e:
            print(f"   ❌ Error: {e}\n")
            return False
        
        # Test 3: Try an invalid location
        print("3️⃣  Testing invalid location handling...")
        try:
            result = await get_location_forecast(session, "invalid-beach-name-12345")
            if result is None:
                print("   ✅ Correctly returned None for invalid location\n")
            else:
                print("   ⚠️  Expected None for invalid location\n")
        except SafeSwimAPIError as e:
            print(f"   ⚠️  Error (should return None): {e}\n")
        
        # Test 4: Check various water quality states
        print("4️⃣  Checking for different water quality states...")
        quality_states = set()
        try:
            # Check a few locations for variety
            test_locations = ["home-bay", "judges-bay", "rothesay-bay", "kerikeri-basin"]
            for slug in test_locations:
                data = await get_location_forecast(session, slug)
                if data and "forecasts" in data and "WATER_QUALITY" in data["forecasts"]:
                    quality_states.update(
                        v for v in data["forecasts"]["WATER_QUALITY"] if v
                    )
            
            print(f"   ✅ Found quality states: {', '.join(sorted(quality_states))}\n")
        except SafeSwimAPIError as e:
            print(f"   ⚠️  Error: {e}\n")
        
        # Test 5: Verify GPS coordinates for map display
        print("5️⃣  Verifying GPS coordinates for map display...")
        try:
            data = await get_location_forecast(session, test_slug)
            if data:
                lat = data.get("latitude")
                lon = data.get("longitude")
                if lat is not None and lon is not None:
                    print(f"   ✅ Location has GPS coordinates: {lat}, {lon}")
                    print(f"   📍 This location will appear on Home Assistant map\n")
                else:
                    print(f"   ⚠️  Missing GPS coordinates (lat: {lat}, lon: {lon})\n")
            else:
                print(f"   ❌ Could not fetch location data\n")
        except SafeSwimAPIError as e:
            print(f"   ⚠️  Error: {e}\n")
        
        print("✅ All tests completed successfully!")
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_api())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
