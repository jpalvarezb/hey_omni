import os
import requests
import time
from helpers import log_info, log_error

# Define weather conditions dictionary at the top for shared use
weather_conditions = {
    0: "Clear",
    1000: "Clear",
    1001: "Cloudy",
    2000: "Fog",
    4001: "Rain",
    5000: "Snow",
    8000: "Thunderstorm"
}

# Cache for storing the last weather request (for a duration of 10 minutes)
weather_cache = {}

# Function to get latitude and longitude for a city using OpenCage API
def get_city_coordinates(city):
    api_key = os.getenv("OPENCAGE_API_KEY")
    if not api_key:
        log_error("Error: OpenCage API key is not set in environment variables.")
        return None, None

    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={api_key}"
        response = requests.get(url).json()
        if response['results']:
            lat = response['results'][0]['geometry']['lat']
            lon = response['results'][0]['geometry']['lng']
            log_info(f"Coordinates for {city}: Latitude {lat}, Longitude {lon}")
            return lat, lon
        else:
            log_error(f"No results found for city: {city}")
            return None, None
    except Exception as e:
        log_error(f"Error fetching city coordinates: {e}")
        return None, None

# Function to cache weather data for 10 minutes
def cache_weather_data(city, weather_data, cache_duration=600):
    weather_cache[city] = {
        "data": weather_data,
        "timestamp": time.time()
    }

# Function to retrieve cached weather data
def get_cached_weather(city):
    if city in weather_cache:
        cached_data = weather_cache[city]
        if time.time() - cached_data["timestamp"] < 600:  # Cache duration of 10 minutes
            return cached_data["data"]
    return None

# Function to get current weather
def get_weather(location=None):
    if not location:
        return "No location provided."
        
    # Clean the location string before processing
    location = location.strip()
    
    cached_weather = get_cached_weather(location)
    if cached_weather:
        return cached_weather

    lat, lon = get_city_coordinates(location)
    if not lat or not lon:
        log_error(f"Could not determine coordinates for '{location}'.")
        return f"Sorry, I couldn't find the weather for {location}. Please check the city name and try again."

    api_key = os.getenv("TOMORROW_API_KEY")
    if not api_key:
        log_error("Tomorrow.io API key is not set in environment variables.")
        return "API key missing."

    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps=current&apikey={api_key}"

    try:
        log_info(f"Requesting weather data from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        log_info(f"API Response: {data}")

        temperature = data['data']['timelines'][0]['intervals'][0]['values']['temperature']
        weather_code = data['data']['timelines'][0]['intervals'][0]['values']['weatherCode']
        weather_description = weather_conditions.get(weather_code, "Unknown conditions")
        weather_info = f"The current weather in {location} is {weather_description} with a temperature of {temperature}°C."

        cache_weather_data(location, weather_info)
        return weather_info
    except requests.exceptions.RequestException as req_err:
        log_error(f"Network error while fetching weather data: {req_err}")
        return "Could not retrieve the weather. Please check your internet connection."
    except Exception as e:
        log_error(f"Unexpected error while fetching weather data: {e}")
        return "An unexpected error occurred while retrieving the weather."

# Function to get weather forecast
def get_forecast(city, period="daily", forecast_count=1):
    cached_weather = get_cached_weather(city)
    if cached_weather:
        return cached_weather

    lat, lon = get_city_coordinates(city)
    if not lat or not lon:
        log_error(f"Could not determine coordinates for '{city}'.")
        return f"Sorry, I couldn't find the forecast for {city or 'your location'}."

    api_key = os.getenv("TOMORROW_API_KEY")
    if not api_key:
        log_error("Tomorrow.io API key is not set in environment variables.")
        return "API key missing."

    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps={period}&apikey={api_key}"

    try:
        log_info(f"Requesting forecast data from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        log_info(f"API Response: {data}")

        forecast_intervals = data['data']['timelines'][0]['intervals'][:forecast_count]
        forecast_descriptions = []
        for interval in forecast_intervals:
            temperature = interval['values']['temperature']
            weather_code = interval['values']['weatherCode']
            weather_description = weather_conditions.get(weather_code, "Unknown conditions")
            forecast_descriptions.append(f"{weather_description} with {temperature}°C")

        forecast_info = f"The {period} forecast for {city} is: " + ", ".join(forecast_descriptions)
        cache_weather_data(city, forecast_info)
        return forecast_info
    except requests.exceptions.RequestException as req_err:
        log_error(f"Network error while fetching forecast data: {req_err}")
        return "Could not retrieve the forecast. Please check your internet connection."
    except Exception as e:
        log_error(f"Unexpected error while fetching forecast data: {e}")
        return "An unexpected error occurred while retrieving the forecast."
