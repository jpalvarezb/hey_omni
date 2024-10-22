import speech_recognition as sr
import pyttsx3
import time
import datetime
import requests

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Function to convert text to speech
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Function to recognize speech
def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Adjusts for background noise
        audio = recognizer.listen(source)  # Captures the audio input
        try:
            # Convert speech to text
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            speak_text("Sorry, I did not understand that.")
        except sr.RequestError:
            print("Error with the speech recognition service.")
            speak_text("Error with the speech recognition service.")

# Function to get latitude and longitude for a city using OpenCage API
def get_city_coordinates(city):
    try:
        api_key = "55854f67848648f385a97be58a6bcc2d"  # OpenCage API key
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
        # Get location data from ipinfo.io
        response = requests.get("https://ipinfo.io").json()
        loc = response['loc']  # This is the lat,lon string
        lat, lon = loc.split(',')
        city = response['city']
        return lat, lon, city
    except Exception as e:
        print(f"Error fetching location and city: {e}")
        return None, None, None

# Function to confirm or override the location
def confirm_location(city):
    speak_text(f"I found your location as {city}. Is this correct? Please say yes or no.")
    confirmation = recognize_speech().lower()
    if "no" in confirmation:
        speak_text("Please tell me the correct city.")
        city = recognize_speech()
        return city
    else:
        return city

# Function to fetch the weather from Tomorrow.io using dynamic location or city input
def get_weather(city=None):
    if city:
        # Get the latitude and longitude for the city
        lat, lon = get_city_coordinates(city)
        if lat is None or lon is None:
            return f"Sorry, I couldn't find the weather for {city}."
    else:
        # Get dynamic location if no city is provided
        lat, lon, city = get_location_and_city()
        if lat is None or lon is None or city is None:
            return "Sorry, I couldn't determine your location."
        
        # Confirm location with the user
        city = confirm_location(city)

    api_key = "x03HmVqCBcTUV1w1KkR5Kwd1HC1RTtX3"  # Tomorrow.io API key

    # Make a request to Tomorrow.io API for current weather data
    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps=current&apikey={api_key}"
    response = requests.get(url).json()

    try:
        # Extract relevant data from the response
        temperature = response['data']['timelines'][0]['intervals'][0]['values']['temperature']
        weather_code = response['data']['timelines'][0]['intervals'][0]['values']['weatherCode']
        
        weather_conditions = {
            0: "Clear",
            1000: "Clear",
            1001: "Cloudy",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            3000: "Light Wind",
            3001: "Wind",
            3002: "Strong Wind",
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
            8000: "Thunderstorm",
        }

        weather_description = weather_conditions.get(weather_code, "Unknown conditions")
        response_text = f"The current weather in {city} is {weather_description} with a temperature of {temperature}°C."
    except KeyError:
        response_text = "I couldn't retrieve the weather. Please try again later."

    return response_text

# Function to handle commands
def handle_command(command):
    # Check for "weather in" command first to avoid conflict
    if "weather in" in command:
        # Extract the city name from the command
        city = command.split("in")[-1].strip()
        response = get_weather(city)

    elif "weather" in command:
        # Get weather using Tomorrow.io API for current location
        response = get_weather()

    elif "what time" in command or "current time" in command:
        # Get current time
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM
        response = f"The current time is {current_time}."

    elif "what's the date" in command or "current date" in command:
        # Get current date with the day of the week
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")  # e.g., Monday, October 21, 2024
        response = f"Today's date is {current_date}."

    elif "set a timer for" in command:
        try:
            # Extract the number and the time unit (seconds, minutes, or hours)
            parts = command.split("for")[1].strip().split()
            time_value = int(parts[0])
            time_unit = parts[1].lower() if len(parts) > 1 else 'seconds'

            # Convert time to seconds based on the unit
            if "second" in time_unit:
                timer_seconds = time_value
                response = f"Setting a timer for {time_value} seconds."
            elif "minute" in time_unit:
                timer_seconds = time_value * 60
                response = f"Setting a timer for {time_value} minutes."
            elif "hour" in time_unit:
                timer_seconds = time_value * 3600
                response = f"Setting a timer for {time_value} hours."
            else:
                response = "I couldn't understand the time unit. Please use seconds, minutes, or hours."
                return response

            speak_text(response)  # Say the response before starting the timer

            # Now start the timer
            time.sleep(timer_seconds)  # Wait for the specified time
            speak_text("Time's up!")  # Say "Time's up!" after the timer finishes
            response = "Timer completed."
        except:
            response = "I couldn't set the timer. Please try again."

    else:
        response = f"You said: {command}. I'm still learning!"

    return response

# Improved function to get the user's name and greet them
def extract_name(name_response):
    """
    Extracts the name from the user's response by assuming it is either the first
    or the last word in the response. This handles cases like "My name is X" or "X is my name".
    """
    # Split the response into words
    words = name_response.split()

    # Common patterns where the name is likely the first or last word
    if "name" in words:
        if "is" in words:
            name_index = words.index("is") + 1  # The name typically follows "is"
        else:
            name_index = -1  # Assume the name is the last word if there's no "is"
    else:
        name_index = -1  # Default to the last word if we can't detect a pattern

    return words[name_index]

def greet_user():
    speak_text("Hello! What is your name?")
    name_response = recognize_speech()
    if name_response:
        name = extract_name(name_response)
        speak_text(f"Hello {name}, how can I assist you today?")
        return name
    else:
        speak_text("I didn't catch your name. Please try again.")
        return greet_user()  # Retry if the name wasn't caught

# Main loop to interact with the user
def main():
    name = greet_user()  # Ask for the user's name and greet them
    while True:
        command = recognize_speech()
        if command:
            if "exit" in command.lower():
                speak_text(f"Goodbye, {name}!")
                break
            else:
                response = handle_command(command.lower())
                print(response)
                # Speak the response if it's not already spoken inside the command handler
                if not "Setting a timer" in response:
                    speak_text(response)

if __name__ == "__main__":
    main()