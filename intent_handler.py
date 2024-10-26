import re
import dateparser
import logging
from word2number import w2n
from adapt.engine import IntentDeterminationEngine
from adapt.intent import IntentBuilder
from datetime import datetime, timedelta
import time
from calendar_module import add_event, list_upcoming_events, update_event, delete_event
from speech_module import speak_text, recognize_speech
from weather_module import get_weather, get_forecast
from helpers import parse_duration, log_info

# Initialize the Adapt engine
engine = IntentDeterminationEngine()
engine.register_entity("Number")

# Register entities for intents

# General Time and Date Entities
engine.register_entity("date", "DateKeyword")
engine.register_entity("time", "TimeKeyword")
engine.register_entity("today", "DateKeyword")
engine.register_entity("now", "TimeKeyword")
engine.register_entity("tomorrow", "DateAdjustmentKeyword")
engine.register_entity("yesterday", "DateAdjustmentKeyword")

# Adjustment Keywords (e.g., 'in' an hour, 'last' week)
engine.register_entity("in", "AdjustmentKeyword")
engine.register_entity("last", "AdjustmentKeyword")
engine.register_entity("next", "AdjustmentKeyword")
engine.register_entity("ago", "AdjustmentKeyword")

# Duration Units (Hours, Days, etc.)
engine.register_entity("second", "DurationKeyword")
engine.register_entity("seconds", "DurationKeyword")
engine.register_entity("minute", "DurationKeyword")
engine.register_entity("minutes", "DurationKeyword")
engine.register_entity("hour", "DurationKeyword")
engine.register_entity("hours", "DurationKeyword")
engine.register_entity("day", "DurationKeyword")
engine.register_entity("days", "DurationKeyword")
engine.register_entity("week", "DurationKeyword")
engine.register_entity("weeks", "DurationKeyword")

# Weather-related entities
engine.register_entity("weather", "WeatherKeyword")
engine.register_entity("forecast", "WeatherKeyword")
engine.register_entity("climate", "WeatherKeyword")
engine.register_entity("what's", "GetKeyword")
engine.register_entity("in", "Location")

# Calendar event-related entities
engine.register_entity("create", "CreateEventKeyword")
engine.register_entity("event", "EventKeyword")
engine.register_entity("update", "UpdateEventKeyword")
engine.register_entity("delete", "DeleteEventKeyword")
engine.register_entity("schedule", "CreateEventKeyword")

# Timer Intent
# Timer Intent with number and time unit entities
set_timer_intent = IntentBuilder("SetTimerIntent") \
    .require("SetKeyword") \
    .require("TimerKeyword") \
    .optionally("Number") \
    .optionally("TimeUnitKeyword") \
    .build()

# Weather Intent
get_weather_intent = IntentBuilder("GetWeatherIntent") \
    .require("WeatherKeyword") \
    .optionally("Location") \
    .build()

# Calendar Intent
create_event_intent = IntentBuilder("CreateEventIntent") \
    .require("CreateEventKeyword") \
    .require("EventKeyword") \
    .build()

update_event_intent = IntentBuilder("UpdateEventIntent") \
    .require("UpdateEventKeyword") \
    .require("EventKeyword") \
    .optionally("Time") \
    .build()

delete_event_intent = IntentBuilder("DeleteEventIntent") \
    .require("DeleteEventKeyword") \
    .require("EventKeyword") \
    .build()

# Register intents with the engine
engine.register_intent_parser(set_timer_intent)
engine.register_intent_parser(get_weather_intent)
engine.register_intent_parser(create_event_intent)
engine.register_intent_parser(update_event_intent)
engine.register_intent_parser(delete_event_intent)

# Set Timer
def handle_set_timer(duration_str, speak_text):
    if not duration_str:
        speak_text("For how long would you like to set the timer?")
        duration_str = recognize_speech()  # Get user input if not present in intent

    parsed_duration = parse_duration(duration_str, speak_text)  # Parsing and error logging handled in helper
    
    if parsed_duration is not None:
        speak_text(f"Setting a timer for {duration_str}.")
        time.sleep(parsed_duration)
        speak_text("Time's up!")
        return f"Timer set for {duration_str}."
    else:
        speak_text("Timer duration was not understood.")
        return "Timer duration was not understood."

# Weather Function
def handle_get_weather(intent):
    # Combine location phrases after 'in'
    raw_location = intent.get("Location")
    location_match = re.search(r"in\s+(.+)", raw_location) if raw_location else None
    location = location_match.group(1).strip() if location_match else raw_location

    if not location:
        logging.info("User did not provide a specific city. Prompting for city name.")
        speak_text("I couldn't determine your current location. Please provide a city name.")
        location = recognize_speech()
        logging.info(f"User provided location: {location}")

    # Check for forecast keywords
    if "forecast" in intent.get("WeatherKeyword", ""):
        speak_text("Would you like a daily or hourly forecast?")
        forecast_type = recognize_speech().lower()
        period = "daily" if "daily" in forecast_type else "hourly"
        speak_text("How many days or hours would you like the forecast for?")
        forecast_count = int(recognize_speech())
        weather_info = get_forecast(city=location, period=period, forecast_count=forecast_count)
    else:
        weather_info = get_weather(city=location)
    
    speak_text(weather_info)
    return weather_info

# Create Event Function (using `datetime` and `timedelta`)
def handle_create_event(intent, service):
    speak_text("Please provide a title for the event.")
    event_title = recognize_speech()

    speak_text("At what time should this event start?")
    start_time_str = recognize_speech()
    start_time = dateparser.parse(start_time_str)

    speak_text("How long will this event last? Provide the duration in hours or minutes.")
    duration_str = recognize_speech()
    duration = parse_duration(duration_str)

    end_time = start_time + timedelta(seconds=duration)

    result = add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
    speak_text(result)
    return result

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

def process_command(command, service, speak_text):
    # Directly handle the exit command first
    if "exit" in command.lower():
        speak_text("Goodbye!")
        return "EXIT"  # Return a specific marker for exit

    # Determine intents based on input command
    for intent in engine.determine_intent(command):
        intent_type = intent.get("intent_type")
        
        if intent_type == "SetTimerIntent":
            # Extract number and unit for duration
            number = intent.get("Number", "")
            time_unit = intent.get("TimeUnitKeyword", "")
            duration_str = f"{number} {time_unit}".strip()
            log_info(f"Extracted duration string: '{duration_str}'")
            return handle_set_timer(duration_str, speak_text)
        elif intent_type == "GetWeatherIntent":
            return handle_get_weather(intent, speak_text)
        elif intent_type == "CreateEventIntent":
            return handle_create_event(intent, service, speak_text)
        elif intent_type == "UpdateEventIntent":
            return handle_update_event(intent, service, speak_text)
        elif intent_type == "DeleteEventIntent":
            return handle_delete_event(intent, service, speak_text)
    
    # If no intent matches
    speak_text("Sorry, I couldn't understand the command.")
    return "I'm sorry, I couldn't understand the command."