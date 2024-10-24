import re
import time
from calendar_module import add_event, list_upcoming_events, update_event, delete_event
from speech_module import speak_text, recognize_speech
from datetime import datetime, timedelta, timezone
from weather_module import get_weather

# Utility function to parse time in '5 PM' or '5:30 PM' format into a 24-hour clock
def parse_time(time_str):
    # Normalize the time string by ensuring correct spaces and uppercasing
    time_str = time_str.strip().upper().replace(".", "")  # Remove periods

    # Check if AM or PM exists, if not raise an error
    if "AM" not in time_str and "PM" not in time_str:
        raise ValueError(f"Time format '{time_str}' is incorrect. It must include AM or PM.")
    
    try:
        # Handle cases where the time includes minutes like '2:30 PM'
        if ':' in time_str:
            time_obj = datetime.strptime(time_str, "%I:%M %p")
        else:
            # Handle simple cases like '2 PM'
            time_obj = datetime.strptime(time_str, "%I %p")
        return time_obj.hour, time_obj.minute
    except ValueError:
        raise ValueError(f"Time format '{time_str}' is incorrect.")

# Function to handle creating events with flexible input
def confirm_event_creation(event_title, start_time, end_time): 
    start_time_str = start_time.strftime("%I:%M %p")
    end_time_str = end_time.strftime("%I:%M %p")
    speak_text(f"You're scheduling an event titled {event_title} from {start_time_str} to {end_time_str}. Should I proceed?")
    confirmation = recognize_speech().lower()
    return "yes" in confirmation

def create_event_conversation(service, command):
    print(f"Debug: Command received: {command}")
    time_pattern = r'(\d{1,2}(?::\d{2})? ?[APap][Mm]?)'  # Time format like 5PM or 5:30PM
    date_time_pattern = r'(tomorrow|today)'  # Date pattern to capture 'tomorrow' or 'today'

    if re.search(time_pattern, command) and re.search(date_time_pattern, command):
        times = re.findall(time_pattern, command)
        event_title_match = re.search(r'(?:titled|named) (\w+)', command)
        event_title = event_title_match.group(1) if event_title_match else "Untitled event"
        start_time = datetime.now() + timedelta(days=1) if "tomorrow" in command else datetime.now()

        try:
            # Debugging: Print the extracted time strings before parsing
            print(f"Debug: Time string(s) extracted: {times}")

            # Normalize and parse the first time
            normalized_time = times[0].strip().upper().replace(".", "").replace("P", " PM").replace("A", " AM")
            print(f"Debug: Normalized time for parsing: '{normalized_time}'")
            start_hour, start_minute = parse_time(normalized_time)
            start_time = start_time.replace(hour=start_hour, minute=start_minute)

            # Set default end time to 1 hour later
            end_time = start_time + timedelta(hours=1)

            # If second time (end time) is given, adjust the end time
            if len(times) > 1:
                normalized_end_time = times[1].strip().upper().replace(".", "").replace("P", " PM").replace("A", " AM")
                print(f"Debug: Normalized end time for parsing: '{normalized_end_time}'")
                end_hour, end_minute = parse_time(normalized_end_time)
                end_time = start_time.replace(hour=end_hour, minute=end_minute)

            # Confirm the event with the user
            if confirm_event_creation(event_title, start_time, end_time):
                response = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())

                # Modify the speak_text call based on whether a second time was provided
                if len(times) > 1:
                    speak_text(f"Event {event_title or 'Untitled event'} scheduled from {times[0]} to {times[1]}")
                else:
                    speak_text(f"Event {event_title or 'Untitled event'} scheduled from {times[0]} to {end_time.strftime('%I:%M %p')}")

                return response
            else:
                return "Event creation canceled."
        except ValueError as e:
            print(f"Error parsing time: {e}")
            speak_text(f"Sorry, I couldn't process the time '{times[0]}'. Please try again.")
            return "Error with event creation."

    # Step 2: Ask follow-up questions if no date or time is detected
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
            try:
                normalized_time = time_match.group().strip().upper().replace(".", "").replace("P", " PM").replace("A", " AM")
                print(f"Debug: Normalized time for parsing: '{normalized_time}'")
                start_hour, start_minute = parse_time(normalized_time)
                start_time = datetime.now().replace(hour=start_hour, minute=start_minute)
                duration = 1  # Default to 1 hour

                if "for an hour" in time_response:
                    duration = 1
                elif "for two hours" in time_response:
                    duration = 2

                end_time = start_time + timedelta(hours=duration)

                # Confirm the event with the user
                if confirm_event_creation(event_title, start_time, end_time):
                    response = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
                    speak_text(f"Event {event_title or 'Untitled event'} scheduled from {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}")
                    return response
                else:
                    return "Event creation canceled."
            except ValueError as e:
                print(f"Error parsing time: {e}")
                speak_text(f"Sorry, I couldn't process the time '{time_match.group()}'. Please try again.")
                return "Error with event creation."

    return "Sorry, I couldn't process your event creation."  # Default return if something goes wrong

# Function to handle commands
def handle_command(command, service, speak_text, recognize_speech):
    if "weather in" in command:
        city = command.split("in")[-1].strip()
        response = get_weather(city=city, recognize_speech=recognize_speech, speak_text=speak_text)

    elif "weather" in command:
        # Pass both speak_text and recognize_speech into get_weather for dynamic city input
        response = get_weather(city=None, recognize_speech=recognize_speech, speak_text=speak_text)
        return response
    
    elif "create event" in command or "schedule event" in command:
        return create_event_conversation(service, command)

    elif "update event" in command:
        summary = command.split("event")[-1].strip().split("to")[0].strip()
        events = list_upcoming_events(service)
        event_id = next((event['id'] for event in events if event['summary'].lower() == summary.lower()), None)
        if event_id:
            start_time = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            response = update_event(service, event_id, updated_summary=summary, updated_start_time=start_time)
        else:
            response = f"Event '{summary}' not found."

    elif "delete event" in command:
        summary = command.split("event")[-1].strip()
        events = list_upcoming_events(service)
        event_id = next((event['id'] for event in events if event['summary'].lower() == summary.lower()), None)
        if event_id:
            response = delete_event(service, event_id)
        else:
            response = f"Event '{summary}' not found."
    
    elif "what time" in command or "what is the time" in command or "what's the time" in command or "current time" in command:
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

            # Ask for user confirmation
            speak_text(f"I understood {response}. Should I proceed?")
            confirmation = recognize_speech().lower()

            if "yes" in confirmation or "proceed" in confirmation:
                speak_text("Okay, starting the timer.")
                print(response)

                # Now start the timer
                time.sleep(timer_seconds)  # Correct use of time.sleep from the time module
                speak_text("Time's up!")  # Say "Time's up!" after the timer finishes
                response = "Timer completed."
            else:
                speak_text("Timer was not set.")
                response = "Timer was canceled."

        except Exception as e:
            print(f"Error setting timer: {e}")
            response = "I couldn't set the timer. Please try again."

    else:
        response = f"Sorry, did you say: {command}?"
    
    return response