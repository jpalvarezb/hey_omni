import re
import dateparser
from timer import set_timer
from adapt.engine import IntentDeterminationEngine
from adapt.intent import IntentBuilder
from datetime import datetime, timedelta
from calendar_module import add_event, list_upcoming_events, update_event, delete_event
from speech_module import speak_text, recognize_speech, recognize_speech_with_cancel_retry
from weather_module import get_weather, get_forecast
from helpers import parse_duration, parse_location_from_command, log_info, log_error

# Initialize the Adapt engine
engine = IntentDeterminationEngine()

# Register entities for intents

# Numerical Entities for Time Calculations
engine.register_entity("one", "NumberKeyword")
engine.register_entity("two", "NumberKeyword")
engine.register_entity("three", "NumberKeyword")
engine.register_entity("five", "NumberKeyword")
engine.register_entity("ten", "NumberKeyword")

# General Time and Date Entities
engine.register_entity("date", "DateKeyword")
engine.register_entity("time", "TimeKeyword")
engine.register_entity("today", "DateKeyword")
engine.register_entity("now", "TimeKeyword")
engine.register_entity("pm", "MeridiemKeyword")
engine.register_entity("am", "MeridiemKeyword")
engine.register_entity("tomorrow", "DateAdjustmentKeyword")
engine.register_entity("yesterday", "DateAdjustmentKeyword")

# Adjustment Keywords for Relative Time Calculations (e.g., 'in' an hour, 'last' week)
engine.register_entity("in", "RelativeTimeKeyword")
engine.register_entity("last", "RelativeTimeKeyword")
engine.register_entity("next", "RelativeTimeKeyword")
engine.register_entity("ago", "RelativeTimeKeyword")

# Duration Units (e.g., Hours, Days, etc.)
engine.register_entity("second", "DurationUnitKeyword")
engine.register_entity("seconds", "DurationUnitKeyword")
engine.register_entity("minute", "DurationUnitKeyword")
engine.register_entity("minutes", "DurationUnitKeyword")
engine.register_entity("hour", "DurationUnitKeyword")
engine.register_entity("hours", "DurationUnitKeyword")
engine.register_entity("day", "DurationUnitKeyword")
engine.register_entity("days", "DurationUnitKeyword")
engine.register_entity("week", "DurationUnitKeyword")
engine.register_entity("weeks", "DurationUnitKeyword")

# Weather-Related Entities
engine.register_entity("weather", "WeatherKeyword")
engine.register_entity("forecast", "WeatherKeyword")
engine.register_entity("climate", "WeatherKeyword")
engine.register_entity("in", "LocationKeyword")

# Misceleanous
engine.register_entity("set", "SetKeyword")
engine.register_entity("timer", "TimerKeyword")
engine.register_entity("Managua", "CityKeyword")
engine.register_entity("New York", "CityKeyword")
engine.register_entity("Miami", "CityKeyword")


# Calendar Event-Related Entities
engine.register_entity("create", "EventActionKeyword")
engine.register_entity("event", "EventTypeKeyword")
engine.register_entity("update", "EventActionKeyword")
engine.register_entity("delete", "EventActionKeyword")
engine.register_entity("schedule", "EventActionKeyword")
engine.register_entity("meeting", "EventNameKeyword")
engine.register_entity("appointment", "EventNameKeyword")

# Intent setup for SetTimerIntent with NumberKeyword as required
set_timer_intent = IntentBuilder("SetTimerIntent") \
    .require("SetKeyword") \
    .require("TimerKeyword") \
    .require("NumberKeyword") \
    .require("DurationUnitKeyword") \
    .build()

# Weather Intent
get_weather_intent = IntentBuilder("GetWeatherIntent") \
    .require("WeatherKeyword") \
    .optionally("LocationKeyword") \
    .optionally("CityKeyword")\
    .optionally("DateAdjustmentKeyword") \
    .optionally("RelativeTimeKeyword") \
    .optionally("TimeKeyword") \
    .optionally("MeridiemKeyword") \
    .build()

# Calendar Intent
create_event_intent = IntentBuilder("CreateEventIntent") \
    .require("EventActionKeyword") \
    .require("EventTypeKeyword") \
    .optionally("DateKeyword") \
    .optionally("DateAdjustmentKeyword") \
    .optionally("TimeKeyword") \
    .build()

update_event_intent = IntentBuilder("UpdateEventIntent") \
    .require("EventActionKeyword") \
    .require("EventTypeKeyword") \
    .optionally("TimeKeyword") \
    .optionally("DateAdjustmentKeyword") \
    .build()

delete_event_intent = IntentBuilder("DeleteEventIntent") \
    .require("EventActionKeyword") \
    .require("EventTypeKeyword") \
    .build()

#Miscellaneous
city_intent = IntentBuilder("CityIntent") \
    .require("CityKeyword") \
    .optionally("Location") \
    .build()

# Register intents with the engine
engine.register_intent_parser(set_timer_intent)
engine.register_intent_parser(get_weather_intent)
engine.register_intent_parser(create_event_intent)
engine.register_intent_parser(update_event_intent)
engine.register_intent_parser(delete_event_intent)

# Weather Function
def handle_get_weather(intent, recognize_speech, speak_text):
    # Step 1: Attempt to get location from CityKeyword, fallback to parsing command text if missing
    command_text = intent.get("command", "")
    raw_location = intent.get("CityKeyword", "")
    location = raw_location.strip() if raw_location else parse_location_from_command(command_text)

    # Only prompt user for location if it's still empty after parsing
    if not location:
        speak_text("Could you please specify the town or city?")
        location = recognize_speech().strip()
        log_info(f"User specified location: {location}")

    # Step 2: Determine forecast period and count based on time-related keywords
    raw_time_input = f"{intent.get('DateAdjustmentKeyword', '')} {intent.get('TimeKeyword', '')} {intent.get('MeridiemKeyword', '')}".strip()
    forecast_period = "daily"  # Default to daily
    forecast_count = 1

    if raw_time_input:
        log_info(f"Parsing time input: {raw_time_input}")
        forecast_date = dateparser.parse(raw_time_input)

        if forecast_date:
            days_difference = (forecast_date - datetime.now()).days
            forecast_count = min(days_difference + 1, 7) if days_difference > 0 else 1

        # Hourly forecast condition
        if any(kw in raw_time_input for kw in ["am", "pm", "hour"]):
            forecast_period = "hourly"
            forecast_count = 24  # Default to 24 hours if hourly

    # Step 3: Determine if a forecast or current weather is requested
    if intent.get("WeatherKeyword") == "forecast":
        speak_text(f"Would you like a {forecast_period} forecast? Please specify the number of days or hours if needed.")
        
        try:
            user_forecast_count = int(recognize_speech().strip())
            forecast_count = min(user_forecast_count, forecast_count)
        except ValueError:
            log_error("Invalid forecast count received from speech input.")
            speak_text("I didn't catch a valid number for the forecast period. Showing default forecast.")

        weather_info = get_forecast(city=location, period=forecast_period, forecast_count=forecast_count)
    else:
        weather_info = get_weather(city=location)

    speak_text(weather_info)
    return weather_info

# Create event function
def handle_create_event(command, service, speak_text):
    # Ensure command is not None
    if not command:
        speak_text("I didn't get the command details. Could you please specify the event details?")
        command = recognize_speech_with_cancel_retry()
        if command == "cancel":
            speak_text("Event creation canceled.")
            return "Event creation canceled."

    # Extract event title, date, time, and duration from command using regex patterns
    title_match = re.search(r"named\s+(.+?)\s+(at|for|tomorrow|today)", command)
    time_match = re.search(r"\bat\s+([\w\s:]+(?:am|pm)?)", command)
    duration_match = re.search(r"for\s+(\d+|one|two|three|five|ten)\s+(hour|minute|hours|minutes)", command)
    date_match = re.search(r"(tomorrow|today|next\s+\w+)", command)

    # Extract matched details or set to None if not found
    event_title = title_match.group(1).strip() if title_match else None
    start_time_str = time_match.group(1).strip() if time_match else None
    duration_str = f"{duration_match.group(1)} {duration_match.group(2)}" if duration_match else None
    event_date = dateparser.parse(date_match.group(0)).date() if date_match else None

    # Combine event date and start time if both are provided
    if event_date and start_time_str:
        start_time = dateparser.parse(f"{event_date} {start_time_str}")
    else:
        start_time = dateparser.parse(start_time_str) if start_time_str else None

    # Parse duration using helper function
    duration = parse_duration(duration_str, speak_text) if duration_str else None

    # Prompt user for missing information
    if not event_title:
        speak_text("Please provide a title for the event.")
        response = recognize_speech_with_cancel_retry()
        if response == "cancel":
            speak_text("Event creation canceled.")
            return "Event creation canceled."
        event_title = response

    if not start_time:
        speak_text("At what time should this event start?")
        response = recognize_speech_with_cancel_retry()
        if response == "cancel":
            speak_text("Event creation canceled.")
            return "Event creation canceled."
        start_time = dateparser.parse(response)

    if not duration:
        speak_text("How long will this event last? Provide the duration in hours or minutes.")
        response = recognize_speech_with_cancel_retry()
        if response == "cancel":
            speak_text("Event creation canceled.")
            return "Event creation canceled."
        duration = parse_duration(response, speak_text)

    # Create the event if all details are valid
    if event_title and start_time and duration:
        end_time = start_time + timedelta(seconds=duration)
        result = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
        speak_text(result)
        return result
    else:
        speak_text("I couldn't create the event due to missing or incorrect details.")
        return "Event creation failed."

# Update Event Function (using `datetime`)
def handle_update_event(intent, service):
    speak_text("Please provide the event name you would like to update.")
    event_name = recognize_speech()

    events = list_upcoming_events(service)
    event_id = next((event['id'] for event in events if event['summary'].lower() == event_name.lower()), None)

    if event_id:
        speak_text("What would you like to update the event to?")
        updated_summary = recognize_speech()

        speak_text("When would you like to start the event?")
        updated_start_time_str = recognize_speech()
        updated_start_time = dateparser.parse(updated_start_time_str)

        result = update_event(service, event_id, updated_summary=updated_summary, updated_start_time=updated_start_time.isoformat())
        speak_text(result)
        return result
    else:
        response = f"Event '{event_name}' not found."
        speak_text(response)
        return response

# Delete Event Function
def handle_delete_event(intent, service):
    speak_text("Please provide the event name you want to delete.")
    event_name = recognize_speech()

    events = list_upcoming_events(service)
    event_id = next((event['id'] for event in events if event['summary'].lower() == event_name.lower()), None)

    if event_id:
        result = delete_event(service, event_id)
        speak_text(result)
        return result
    else:
        response = f"Event '{event_name}' not found."
        speak_text(response)
        return response

# Process command
def process_command(command, service, speak_text):
    """Processes the recognized command and logs parsing details."""
    log_info(f"Processing command: {command}")

    # Directly handle the "exit" command to return the "EXIT" marker
    if "exit" in command.lower():
        speak_text("Goodbye!")
        log_info("Exiting program as per user command.")
        return "EXIT"  # Return a specific marker to exit the main loop

    for intent in engine.determine_intent(command):
        intent_type = intent.get("intent_type")
        log_info(f"Detected intent type: {intent_type}")
        log_info(f"Intent details: {intent}")

        # Check if SetTimerIntent is correctly detected
        if intent_type == "SetTimerIntent":
            number = intent.get("NumberKeyword", "")
            time_unit = intent.get("DurationUnitKeyword", "")
            duration_str = f"{number} {time_unit}".strip()

            log_info(f"Extracted duration string: '{duration_str}'")
            return set_timer(duration_str, speak_text)
        
        # Other intents
        elif intent_type == "GetWeatherIntent":
            return handle_get_weather(intent, recognize_speech, speak_text)
        
        elif intent_type == "CreateEventIntent":
            return handle_create_event(command, service, speak_text)
        
        elif intent_type == "UpdateEventIntent":
            return handle_update_event(intent, service)
        
        elif intent_type == "DeleteEventIntent":
            return handle_delete_event(intent, service)

    # No intent recognized, log error and inform user
    log_error("Failed to match a command to any intent.")
    speak_text("Sorry, I couldn't understand the command.")
    return "I'm sorry, I couldn't understand the command."  
    
