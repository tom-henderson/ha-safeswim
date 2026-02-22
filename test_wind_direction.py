#!/usr/bin/env python3
"""Test wind direction compass conversion."""

def get_compass_direction(degrees: float) -> str:
    """Convert wind direction degrees to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(degrees / 22.5) % 16
    return directions[index]


def test_compass_directions():
    """Test various degree values."""
    test_cases = [
        (0, "N"),
        (22.5, "NNE"),
        (45, "NE"),
        (90, "E"),
        (135, "SE"),
        (180, "S"),
        (225, "SW"),
        (239, "WSW"),
        (270, "W"),
        (315, "NW"),
        (350, "N"),
        (360, "N"),
    ]
    
    print("Testing wind direction conversion:")
    print("=" * 50)
    
    all_passed = True
    for degrees, expected in test_cases:
        result = get_compass_direction(degrees)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} {degrees:6.1f}° → {result:4s} (expected {expected})")
    
    print("=" * 50)
    
    # Show all 16 directions
    print("\nAll 16 compass directions:")
    print("=" * 50)
    for i in range(16):
        degrees = i * 22.5
        direction = get_compass_direction(degrees)
        print(f"{degrees:6.1f}° → {direction}")
    
    print("=" * 50)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = test_compass_directions()
    exit(0 if success else 1)
