import os
import requests
import time
from helpers import log_info, log_error  # Using centralized logging from helpers

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
def get_weather(city=None, recognize_speech=None, speak_text=None):
    cached_weather = get_cached_weather(city)
    if cached_weather:
        return cached_weather

    lat, lon = get_city_coordinates(city)
    if not lat or not lon:
        log_error(f"Could not determine coordinates for '{city}'.")
        return f"Sorry, I couldn't find the weather for {city or 'your location'}."

    api_key = os.getenv("TOMORROW_API_KEY")
    if not api_key:
        raise ValueError("Tomorrow.io API key is not set in environment variables.")
    
    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps=current&apikey={api_key}"
    
    try:
        log_info(f"Requesting weather data from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        log_info(f"API Response: {data}")

        try:
            temperature = data['data']['timelines'][0]['intervals'][0]['values']['temperature']
            weather_code = data['data']['timelines'][0]['intervals'][0]['values']['weatherCode']
            weather_conditions = {
                0: "Clear",
                1000: "Clear",
                1001: "Cloudy",
                2000: "Fog",
                4001: "Rain",
                5000: "Snow",
                8000: "Thunderstorm"
            }
            weather_description = weather_conditions.get(weather_code, "Unknown conditions")
            weather_info = f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C."

            cache_weather_data(city, weather_info)
            return weather_info
        except KeyError as e:
            log_error(f"Key error in parsing weather data: {e}")
            return "I couldn't retrieve the weather. Please try again later."

    except requests.exceptions.RequestException as req_err:
        log_error(f"Network error while fetching weather data: {req_err}")
        return "I couldn't retrieve the weather. Please check your internet connection and try again."
    except Exception as e:
        log_error(f"Unexpected error while fetching weather data: {e}")
        return "An unexpected error occurred while retrieving the weather."


# Function to get weather forecast
def get_forecast(city=None, period="daily", forecast_count=1, recognize_speech=None, speak_text=None):
    lat, lon = get_city_coordinates(city) if city else (None, None)
    
    if not lat or not lon:
        log_error(f"Could not determine coordinates for '{city}'.")
        return f"Sorry, I couldn't find the forecast for {city or 'your location'}."

    api_key = os.getenv("TOMORROW_API_KEY")
    if not api_key:
        raise ValueError("Tomorrow.io API key is not set in environment variables.")

    timesteps = "1d" if period == "daily" else "1h"
    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps={timesteps}&apikey={api_key}"
    
    try:
        log_info(f"Requesting forecast data from URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        log_info(f"API Response: {data}")

        forecast = []
        intervals = data['data']['timelines'][0]['intervals'][:forecast_count]
        weather_conditions = {
            0: "Clear",
            1000: "Clear",
            1001: "Cloudy",
            2000: "Fog",
            4001: "Rain",
            5000: "Snow",
            8000: "Thunderstorm"
        }

        for interval in intervals:
            time = interval['startTime']
            temperature = interval['values'].get('temperature', 'N/A')
            weather_code = interval['values'].get('weatherCode', None)
            weather_description = weather_conditions.get(weather_code, "Unknown conditions")
            forecast.append(f"{time}: {weather_description}, {temperature}°C")

        return f"The forecast for {city} is: " + ", ".join(forecast)

    except requests.exceptions.RequestException as req_err:
        log_error(f"Network error while fetching forecast: {req_err}")
        return "I couldn't retrieve the forecast. Please check your internet connection and try again."
    except Exception as e:
        log_error(f"Unexpected error while fetching forecast: {e}")
        return "An unexpected error occurred while retrieving the forecast."