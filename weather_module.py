import requests

# Function to get latitude and longitude for a city using OpenCage API
def get_city_coordinates(city):
    try:
        api_key = "55854f67848648f385a97be58a6bcc2d"
        url = f"https://api.opencagedata.com/geocode/v1/json?q={city}&key={api_key}"
        response = requests.get(url).json()
        if response['results']:
            lat = response['results'][0]['geometry']['lat']
            lon = response['results'][0]['geometry']['lng']
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching city coordinates: {e}")
        return None, None

# Function to get the user's location dynamically using ipinfo.io
def get_location_and_city():
    try:
        response = requests.get("https://ipinfo.io").json()
        loc = response['loc']
        lat, lon = loc.split(',')
        city = response['city']
        return lat, lon, city
    except Exception as e:
        print(f"Error fetching location and city: {e}")
        return None, None, None

# Function to confirm or override the location
def confirm_location(city, recognize_speech, speak_text):
    speak_text(f"I found your location as {city}. Is this correct? Please say yes or no.")
    confirmation = recognize_speech()

    if confirmation:
        confirmation = confirmation.lower()
        if "no" in confirmation:
            speak_text("Please tell me the correct city.")
            city = recognize_speech()
            return city
        else:
            return city
    else:
        speak_text("I didn't hear that. Please try again.")
        return confirm_location(city, recognize_speech, speak_text)  # Retry if no response was captured

# Function to fetch the weather from Tomorrow.io using dynamic location or city input
def get_weather(city=None, recognize_speech=None, speak_text=None):
    if city:
        # Fetch coordinates for the provided city
        lat, lon = get_city_coordinates(city)
        if lat is None or lon is None:
            return f"Sorry, I couldn't find the weather for {city}."
    else:
        # Try to get the user's current location using IP geolocation
        lat, lon, current_city = get_location_and_city()
        
        if lat is None or lon is None or current_city is None:
            # If location cannot be fetched, ask for city input
            speak_text("I couldn't determine your current location. Please provide a city name.")
            city = recognize_speech()
            lat, lon = get_city_coordinates(city)
            if lat is None or lon is None:
                return f"Sorry, I couldn't find the weather for {city}."
        else:
            # Confirm current location with the user
            speak_text(f"I found your location as {current_city}. Is this correct? Please say yes or no.")
            confirmation = recognize_speech()
            
            if "no" in confirmation.lower():
                speak_text("Please tell me the correct city.")
                city = recognize_speech()
                lat, lon = get_city_coordinates(city)
                if lat is None or lon is None:
                    return f"Sorry, I couldn't find the weather for {city}."
            else:
                city = current_city  # Use the confirmed current location

    # Fetch the weather from Tomorrow.io using the determined latitude and longitude
    api_key = "x03HmVqCBcTUV1w1KkR5Kwd1HC1RTtX3"
    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps=current&apikey={api_key}"
    response = requests.get(url).json()

    try:
        temperature = response['data']['timelines'][0]['intervals'][0]['values']['temperature']
        weather_code = response['data']['timelines'][0]['intervals'][0]['values']['weatherCode']
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
        return f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C."
    except KeyError:
        return "I couldn't retrieve the weather. Please try again later."