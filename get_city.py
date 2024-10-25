# test_location_and_city.py

import os
import logging
from weather_module import get_location_and_city

logging.basicConfig(level=logging.INFO)

# Set your IPINFO_API_KEY in the environment for IP-based location testing
os.environ["IPINFO_API_KEY"] = "630b60c0f8acd5"  # Replace with your actual key

# Test case: "your current location"
lat, lon, city = get_location_and_city("your current location")
if lat and lon:
    print(f"Test 'your current location': Latitude = {lat}, Longitude = {lon}, City = {city}")
else:
    print("Failed to retrieve location for 'your current location'.")

# Test case: Specified city
lat, lon, city = get_location_and_city("New York City")
if lat and lon:
    print(f"Test 'New York City': Latitude = {lat}, Longitude = {lon}, City = {city}")
else:
    print("Failed to retrieve location for 'New York City'.")