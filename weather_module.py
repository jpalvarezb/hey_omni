import os
import requests
import time
from datetime import datetime, timedelta
from helpers import log_info, log_error

# Expanded weather conditions dictionary
weather_conditions = {
    0: "Clear",
    1000: "Clear",
    1001: "Cloudy",
    1100: "Mostly Clear",
    1101: "Partly Cloudy",
    1102: "Mostly Cloudy",
    2000: "Fog",
    2100: "Light Fog",
    4000: "Drizzle",
    4001: "Rain",
    4200: "Light Rain",
    4201: "Heavy Rain",
    5000: "Snow",
    5001: "Flurries",
    5100: "Light Snow",
    5101: "Heavy Snow",
    6000: "Freezing Drizzle",
    6001: "Freezing Rain",
    6200: "Light Freezing Rain",
    6201: "Heavy Freezing Rain",
    7000: "Ice Pellets",
    7101: "Heavy Ice Pellets",
    7102: "Light Ice Pellets",
    8000: "Thunderstorm"
}

# Cache for storing the last weather request (for a duration of 10 minutes)
weather_cache = {}

# Add near the top of the file, after imports
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
TOMORROW_API_KEY = os.getenv("TOMORROW_API_KEY")

# Function to get latitude and longitude for a city using OpenCage API
def get_city_coordinates(city):
    if not OPENCAGE_API_KEY:
        log_error("Error: OpenCage API key is not set in environment variables.")
        return None, None

    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={OPENCAGE_API_KEY}"
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
        
    location = location.strip()
    cached_weather = get_cached_weather(location)
    if cached_weather:
        return cached_weather

    lat, lon = get_city_coordinates(location)
    if not lat or not lon:
        return f"Sorry, I couldn't find the weather for {location}."

    if not TOMORROW_API_KEY:
        return "API key missing."

    try:
        # Request current conditions
        current_url = (f"https://api.tomorrow.io/v4/timelines"
               f"?location={lat},{lon}"
               f"&fields=temperature,weatherCode"
               f"&timesteps=current"
               f"&apikey={TOMORROW_API_KEY}")
        
        # Request daily forecast (separate request for better accuracy)
        daily_url = (f"https://api.tomorrow.io/v4/timelines"
               f"?location={lat},{lon}"
               f"&fields=temperatureMax,temperatureMin,weatherCode"
               f"&timesteps=1d"
               f"&apikey={TOMORROW_API_KEY}")

        # Get current conditions
        current_response = requests.get(current_url)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        current = current_data['data']['timelines'][0]['intervals'][0]['values']
        current_temp = current['temperature']
        current_code = current['weatherCode']
        
        # Get daily forecast
        daily_response = requests.get(daily_url)
        daily_response.raise_for_status()
        daily_data = daily_response.json()
        
        daily = daily_data['data']['timelines'][0]['intervals'][0]['values']
        high_temp = daily.get('temperatureMax')
        low_temp = daily.get('temperatureMin')
        main_code = daily.get('weatherCode')
        
        # Validate temperatures
        if high_temp is None or low_temp is None or high_temp == low_temp:
            log_error(f"Invalid temperature range received: high={high_temp}, low={low_temp}")
            # Try to estimate range based on current temperature
            high_temp = round(current_temp + 2, 1)
            low_temp = round(current_temp - 2, 1)
        
        weather_desc = weather_conditions.get(current_code, "Unknown conditions")
        main_desc = weather_conditions.get(main_code, "Unknown conditions")
        
        weather_info = (
            f"Current conditions in {location}: {weather_desc} with {current_temp}°C. "
            f"Today will be mostly {main_desc} with a high of {high_temp}°C "
            f"and a low of {low_temp}°C."
        )
        
        cache_weather_data(location, weather_info)
        return weather_info
        
    except Exception as e:
        log_error(f"Error fetching weather: {e}")
        return "An error occurred while fetching the weather."

# Function to get weather forecast
def get_forecast(location, period="daily", forecast_count=5, start_offset=0):
    try:
        api_key = os.getenv("TOMORROW_API_KEY")
        if not api_key:
            return "API key missing."
            
        lat, lon = get_city_coordinates(location)
        if not lat or not lon:
            return f"Could not find coordinates for {location}"
            
        log_info(f"Coordinates for {location}: Latitude {lat}, Longitude {lon}")
        
        # Calculate time windows
        now = datetime.utcnow()
        start_time = now + timedelta(days=start_offset)
        end_time = start_time + timedelta(days=forecast_count if period == "daily" else 1)
        
        # Adjust fields and timesteps based on period
        if period == "hourly":
            fields = "temperature,weatherCode"
            timesteps = "1h"
            units = "metric"
        else:
            fields = "temperature,temperatureMax,temperatureMin,weatherCode"
            timesteps = "1d"
            units = "metric"
        
        url = (f"https://api.tomorrow.io/v4/timelines"
               f"?location={lat},{lon}"
               f"&fields={fields}"
               f"&timesteps={timesteps}"
               f"&startTime={start_time.isoformat()}Z"
               f"&endTime={end_time.isoformat()}Z"
               f"&units={units}"
               f"&apikey={api_key}")
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        intervals = data['data']['timelines'][0]['intervals']
        
        if period == "hourly":
            forecast_info = f"Hourly forecast for {location}:"
            for interval in intervals:
                time = datetime.fromisoformat(interval['startTime'].replace('Z', '+00:00'))
                values = interval['values']
                temp = values['temperature']
                desc = weather_conditions.get(values['weatherCode'], "Unknown conditions")
                forecast_info += f"\n{time.strftime('%I:%M %p')}: {desc}, {temp}°C"
        else:
            forecast_info = f"{forecast_count}-day forecast for {location}:"
            for interval in intervals:
                time = datetime.fromisoformat(interval['startTime'].replace('Z', '+00:00'))
                values = interval['values']
                temp = values.get('temperature', None)
                temp_max = values.get('temperatureMax', temp)
                temp_min = values.get('temperatureMin', temp)
                desc = weather_conditions.get(values['weatherCode'], "Unknown conditions")
                
                if start_offset == 1 and forecast_count == 1:
                    forecast_info = f"Tomorrow's forecast for {location}:"
                
                forecast_info += f"\n{time.strftime('%A')}: {desc}, High: {temp_max}°C, Low: {temp_min}°C"
        
        forecast_info = format_weather_response(forecast_info, period)
        return forecast_info
        
    except Exception as e:
        log_error(f"Error fetching forecast: {e}")
        return "An error occurred while fetching the forecast."

def format_weather_response(forecast_data, period="daily"):
    """
    Formats weather forecast data into easily speakable chunks
    Returns a list of strings that can be spoken sequentially
    """
    try:
        if not forecast_data:
            return ["Sorry, I couldn't get the forecast data."]

        responses = []
        forecasts = forecast_data.split('\n')
        
        if period == "hourly":
            # Add header first
            responses.append(forecasts[0])  # Location/forecast type
            
            # Group remaining forecasts in chunks of 3 hours
            for i in range(1, len(forecasts), 3):
                chunk = forecasts[i:i+3]
                responses.append('. '.join(chunk))
        else:
            # For daily forecasts, return as single response
            responses.append(forecast_data)
            
        return responses
            
    except Exception as e:
        log_error(f"Error formatting weather response: {e}")
        return ["Sorry, I had trouble formatting the forecast."]
