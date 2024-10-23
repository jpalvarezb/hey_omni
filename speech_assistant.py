import speech_recognition as sr
import pyttsx3
import time
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import requests
import re

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# SCOPES for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Function to convert text to speech
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Authenticate with Google Calendar
def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('calendar', 'v3', credentials=creds)
    return service

# Function to list upcoming events (for update/delete reference)
def list_upcoming_events(service):
    now = datetime.now(timezone.utc).isoformat()
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# Add event to Google Calendar
def add_event(service, summary, start_time, end_time):
    print(f"Event '{summary}' scheduled from {start_time} to {end_time}.")
    return f"Event '{summary}' created."

# Utility function to parse time in '5 PM' or '5:30 PM' format into a 24-hour clock
def parse_time(time_str):
    # Normalize the time string by removing spaces and making it uppercase
    time_str = time_str.strip().upper().replace(".", "").replace(" ", "")
    
    # Ensure there is an "AM" or "PM" in the string, otherwise raise an error
    if "AM" not in time_str and "PM" not in time_str:
        raise ValueError(f"Time format '{time_str}' is incorrect. It must include AM or PM.")
    
    try:
        # Handle cases where the time includes minutes like '2:30 PM'
        if ':' in time_str:
            time_obj = datetime.strptime(time_str, "%I:%M%p")
        else:
            # Handle simple cases like '2 PM'
            time_obj = datetime.strptime(time_str, "%I%p")
        return time_obj.hour, time_obj.minute
    except ValueError:
        raise ValueError(f"Time format '{time_str}' is incorrect.")

# Function to handle creating events with flexible input
def create_event_conversation(service, command):
    print(f"Debug: Command received: {command}")

    # Extract event title and time using regular expressions
    event_title = None
    time_pattern = r'(\d{1,2}(?::\d{2})? ?[APap][Mm]?)'  # Adjusted time pattern for '5PM', '5:30PM', '2p'
    date_time_pattern = r'tomorrow|today'

    if re.search(time_pattern, command) and re.search(date_time_pattern, command):
        print(f"Debug: Time and date found in the command.")

        times = re.findall(time_pattern, command)  # Find all times
        event_title_match = re.search(r'(?:titled|named) (\w+)', command)  # Look for event title

        if event_title_match:
            event_title = event_title_match.group(1)  # Extract the title
        else:
            event_title = "Untitled event"  # Default to untitled

        # Normalize and parse time
        times = [time.strip().upper().replace(".", "").replace(" ", "") for time in times]
        
        # Convert times into datetime objects
        if "tomorrow" in command:
            start_time = datetime.now() + timedelta(days=1)
        else:
            start_time = datetime.now()

        # Get the parsed hour and minute from the time string
        start_hour, start_minute = parse_time(times[0])
        start_time = start_time.replace(hour=start_hour, minute=start_minute)

        end_time = start_time + timedelta(hours=1)  # Default duration 1 hour

        if len(times) > 1:  # If end time is provided
            end_hour, end_minute = parse_time(times[1])
            end_time = start_time.replace(hour=end_hour, minute=end_minute)

        # Now add event
        response = add_event(service, event_title or "Untitled event", start_time.isoformat(), end_time.isoformat())
        speak_text(f"Event {event_title or 'Untitled event'} scheduled for tomorrow at {times[0]} to {times[1]}")
        return response

    # If time/date is missing, prompt for more information
    else:
        print("Debug: No date or time detected in command.")
        speak_text("Sure, what's the name of the event, at what time, and how long?")
        name_response = recognize_speech() or "Untitled event"
        time_response = recognize_speech() or ""

        # If no title, set it as Untitled
        if "no title" in name_response.lower():
            event_title = "Untitled event"
        else:
            event_title = name_response

        time_match = re.search(time_pattern, time_response)
        if time_match:
            start_hour, start_minute = parse_time(time_match.group())
            start_time = datetime.now().replace(hour=start_hour, minute=start_minute)
            duration = 1  # Default to 1 hour

            if "for an hour" in time_response:
                duration = 1
            elif "for two hours" in time_response:
                duration = 2

            end_time = start_time + timedelta(hours=duration)

            # Add event
            response = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
            speak_text(f"{event_title} scheduled for {time_match.group()} for {duration} hour(s)")
            return response

    return "Sorry, I couldn't process your event creation."  # Default return if something goes wrong

# Function to handle creating events with flexible input
def create_event_conversation(service, command):
    print(f"Debug: Command received: {command}")

    # Extract event title and time using regular expressions
    event_title = None
    time_pattern = r'(\d{1,2}(?::\d{2})? ?[APap][Mm]?)'  # Adjusted time pattern for '5PM', '5:30PM', '2p'
    date_time_pattern = r'tomorrow|today'

    # Step 1: Handle direct command "create an event for me at X"
    if re.search(time_pattern, command) and re.search(date_time_pattern, command):
        print(f"Debug: Time and date found in the command.")

        times = re.findall(time_pattern, command)  # Find all times
        event_title_match = re.search(r'(?:titled|named) (\w+)', command)  # Look for event title

        if event_title_match:
            event_title = event_title_match.group(1)  # Extract the title
        else:
            event_title = "Untitled event"  # Default to untitled

        # Convert times into datetime objects
        if "tomorrow" in command:
            start_time = datetime.now() + timedelta(days=1)
        else:
            start_time = datetime.now()

        # Use parse_time to correctly interpret the time strings
        start_time = start_time.replace(hour=parse_time(times[0]), minute=0)
        end_time = start_time + timedelta(hours=1)  # Default duration 1 hour

        if len(times) > 1:  # If end time is provided
            end_time = start_time.replace(hour=parse_time(times[1]))

        # Now add event
        response = add_event(service, event_title or "Untitled event", start_time.isoformat(), end_time.isoformat())
        speak_text(f"Event {event_title or 'Untitled event'} scheduled for tomorrow at {times[0]} to {times[1]}")
        return response

    # Step 2: If user doesn't provide enough info, ask follow-up questions
    else:
        print("Debug: No date or time detected in command.")
        speak_text("Sure, what's the name of the event, at what time, and how long?")
        name_response = recognize_speech() or "Untitled event"  # Handle None case with default "Untitled event"
        time_response = recognize_speech() or ""  # Handle None case

        # If no title, set it as Untitled
        if "no title" in name_response.lower():
            event_title = "Untitled event"
        else:
            event_title = name_response

        time_match = re.search(time_pattern, time_response)
        if time_match:
            start_time = datetime.now().replace(hour=parse_time(time_match.group()), minute=0)
            duration = 1  # Default to 1 hour

            if "for an hour" in time_response:
                duration = 1
            elif "for two hours" in time_response:
                duration = 2

            end_time = start_time + timedelta(hours=duration)

            # Add event
            response = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
            speak_text(f"{event_title} scheduled for {time_match.group()} for {duration} hour(s)")
            return response

    return "Sorry, I couldn't process your event creation."  # Default return if something goes wrong

# Update an existing event
def update_event(service, event_id, updated_summary=None, updated_start_time=None, updated_end_time=None):
    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    if updated_summary:
        event['summary'] = updated_summary
    if updated_start_time:
        event['start']['dateTime'] = updated_start_time
    if updated_end_time:
        event['end']['dateTime'] = updated_end_time
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
    return f"Event '{updated_summary}' updated."

# Delete an event from Google Calendar
def delete_event(service, event_id):
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return f"Event with ID {event_id} deleted successfully."
    except Exception as e:
        return f"Error occurred: {e}"

# Function to recognize speech
def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.energy_threshold = 300  # Adjust sensitivity to background noise
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            # Attempt to recognize speech
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            speak_text("Sorry, I did not understand that. Please repeat.")
            return ""  # Return an empty string if speech was not understood
        except sr.RequestError:
            print("Error with the speech recognition service.")
            speak_text("There was a problem with the speech service. Please try again.")
            return None  # Return None if there's an issue with the service

# Optional retry mechanism if speech isn't recognized the first time
def recognize_speech_with_retry(attempts=3):
    for _ in range(attempts):
        result = recognize_speech()
        if result:  # If a valid result is returned, exit the loop
            return result
        speak_text("Let me try that again.")
    speak_text("Sorry, I couldn't understand you after several attempts.")
    return None  # Return None after exceeding the retry attempts

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
        response = requests.get("https://ipinfo.io").json()
        loc = response['loc']
        lat, lon = loc.split(',')
        city = response['city']
        return lat, lon, city
    except Exception as e:
        print(f"Error fetching location and city: {e}")
        return None, None, None

# Function to confirm or override the location
def confirm_location(city):
    speak_text(f"I found your location as {city}. Is this correct? Please say yes or no.")
    confirmation = recognize_speech()

    if confirmation:  # Only proceed if there is a valid response
        confirmation = confirmation.lower()
        if "no" in confirmation:
            speak_text("Please tell me the correct city.")
            city = recognize_speech()
            return city
        else:
            return city
    else:
        speak_text("I didn't hear that. Please try again.")
        return confirm_location(city)  # Retry if no response was captured

# Function to fetch the weather from Tomorrow.io using dynamic location or city input
def get_weather(city=None):
    if city:
        lat, lon = get_city_coordinates(city)
        if lat is None or lon is None:
            return f"Sorry, I couldn't find the weather for {city}."
    else:
        lat, lon, city = get_location_and_city()
        if lat is None or lon is None or city is None:
            return "Sorry, I couldn't determine your location."
        
        city = confirm_location(city)

    api_key = "x03HmVqCBcTUV1w1KkR5Kwd1HC1RTtX3"  # Tomorrow.io API key

    url = f"https://api.tomorrow.io/v4/timelines?location={lat},{lon}&fields=temperature&fields=weatherCode&timesteps=current&apikey={api_key}"
    response = requests.get(url).json()

    try:
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
def handle_command(command, service):
    if "weather in" in command:
        city = command.split("in")[-1].strip()
        response = get_weather(city)

    elif "weather" in command:
        response = get_weather()

    elif "create event" in command or "schedule event" in command:
        return create_event_conversation(service, command)

    elif "update the event" in command:
        summary = command.split("event")[-1].strip().split("to")[0].strip()
        events = list_upcoming_events(service)
        event_id = next((event['id'] for event in events if event['summary'].lower() == summary.lower()), None)
        if event_id:
            start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            response = update_event(service, event_id, updated_summary=summary, updated_start_time=start_time)
        else:
            response = f"Event '{summary}' not found."

    elif "delete the event" in command:
        summary = command.split("event")[-1].strip()
        events = list
        events = list_upcoming_events(service)
        event_id = next((event['id'] for event in events if event['summary'].lower() == summary.lower()), None)
        if event_id:
            response = delete_event(service, event_id)
        else:
            response = f"Event '{summary}' not found."
    
    elif "what time" in command or "current time" in command:
        # Get current time
        current_time = datetime.now().strftime("%I:%M %p")  # 12-hour format with AM/PM
        response = f"The current time is {current_time}."

    elif "what's the date" in command or "current date" in command or "what day is it" in command:
        # Get current date with the day of the week
        current_date = datetime.now().strftime("%A, %B %d, %Y")  # e.g., Monday, October 23, 2024
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
    service = authenticate_google_calendar()  # Authenticate with Google Calendar
    name = greet_user()  # Ask for the user's name and greet them
    while True:
        command = recognize_speech()
        if command:
            if "exit" in command.lower():
                speak_text(f"Goodbye, {name}!")
                break
            else:
                response = handle_command(command.lower(), service)
                print(response)
                speak_text(response)

if __name__ == "__main__":
    main()