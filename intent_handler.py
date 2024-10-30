import re
import dateparser
from timer import set_timer
from adapt.engine import IntentDeterminationEngine
from adapt.intent import IntentBuilder
from datetime import datetime, timedelta
from calendar_module import add_event, list_upcoming_events, update_event, delete_event, find_event_by_title
from speech_module import recognize_speech_with_cancel_retry, speak_text, contextual_recognizer
from weather_module import get_weather, get_forecast
from helpers import parse_duration, parse_city, log_info, log_error, parse_time_with_context, format_duration


# Initialize the Adapt engine
engine = IntentDeterminationEngine()

# Register entities for intents

# Add event name registration (near the top with other entity registrations)
engine.register_regex_entity("named (?P<EventName>.*?)(?:\\s+to\\s+|$)")

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
engine.register_entity("hourly", "TimeUnitKeyword")
engine.register_entity("hour", "TimeUnitKeyword")
engine.register_entity("hours", "TimeUnitKeyword")

# Misceleanous
engine.register_entity("set", "SetKeyword")
engine.register_entity("timer", "TimerKeyword")
engine.register_entity("Managua", "CityKeyword")
engine.register_entity("New York", "CityKeyword")
engine.register_entity("Miami", "CityKeyword")


# Calendar Event-Related Entities
engine.register_entity("create", "CreateEventKeyword")
engine.register_entity("event", "EventTypeKeyword")
engine.register_entity("update", "EventActionKeyword")
engine.register_entity("delete", "EventActionKeyword")
engine.register_entity("schedule", "CreateEventKeyword")
engine.register_entity("edit", "EventActionKeyword")
engine.register_entity("modify", "EventActionKeyword")
engine.register_entity("change", "EventActionKeyword")
engine.register_entity("appointment", "EventTypeKeyword")
engine.register_entity("meeting", "EventTypeKeyword")

# Number Keywords (extend for weather forecasts)
engine.register_entity("one", "NumberKeyword")
engine.register_entity("two", "NumberKeyword")
engine.register_entity("three", "NumberKeyword")
engine.register_entity("four", "NumberKeyword")
engine.register_entity("six", "NumberKeyword")
engine.register_entity("seven", "NumberKeyword")
engine.register_entity("eight", "NumberKeyword")
engine.register_entity("nine", "NumberKeyword")
engine.register_entity("ten", "NumberKeyword")

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
    .optionally("CityKeyword") \
    .optionally("DateAdjustmentKeyword") \
    .optionally("RelativeTimeKeyword") \
    .optionally("TimeKeyword") \
    .optionally("TimeUnitKeyword") \
    .optionally("NumberKeyword") \
    .optionally("MeridiemKeyword") \
    .build()

# Calendar Intents
create_event_intent = IntentBuilder("CreateEventIntent") \
    .require("CreateEventKeyword") \
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
    .optionally("EventName") \
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

# Register intents with the engine - order matters!
engine.register_intent_parser(create_event_intent)
engine.register_intent_parser(update_event_intent) 
engine.register_intent_parser(delete_event_intent)
engine.register_intent_parser(set_timer_intent)
engine.register_intent_parser(get_weather_intent)

def get_user_input(prompt_text, validate_func=None, cancel_message="Operation canceled.", context=None):
    """
    Helper function to handle user interaction flow.
    Returns tuple of (success, response)
    """
    speak_text(prompt_text)
    response = recognize_speech_with_cancel_retry(context=context)
    
    if response == "cancel":
        return False, cancel_message
        
    if validate_func and not validate_func(response):
        return False, None
        
    return True, response

# Weather Function
def handle_get_weather(intent, recognize_speech_with_cancel_retry, speak_text, location=None, city=None):
    # Get the command from either the utterance or the raw text
    command = intent.get('utterance', '') or intent.get('command', '')
    log_info(f"Processing weather request with command: {command}")
    
    # First try to get location from parameters or intent
    location = location or city or intent.get("CityKeyword")
    log_info(f"Location from parameters/intent: {location}")
    
    # If not found, try parsing from command
    if not location and command:
        location = parse_city(command, remove_time_words=True)
        log_info(f"Location parsed from command: {location}")
    
    # If still no location found, ask the user
    if not location:
        speak_text("What city would you like the weather for?")
        city_response = recognize_speech_with_cancel_retry(context='weather')
        if city_response == "cancel":
            return "Weather request cancelled."
        location = parse_city(city_response, remove_time_words=True)
        if not location:
            return "I couldn't understand the city name."
        log_info(f"Got city from follow-up: {location}")
    
    # Determine the type of weather request
    request_type = 'current'  # default
    forecast_count = 5  # default
    period = 'daily'  # default
    start_offset = 0  # default
    
    command_lower = command.lower()
    
    # Check for hourly forecast in misrecognitions first
    if any(phrase in command_lower for phrase in ['our lee', 'our leave', 'early']):
        log_info("Detected potential hourly forecast request from misrecognition")
        request_type = 'forecast'
        period = 'hourly'
        forecast_count = 24
    # Then check other time-related keywords
    elif 'tomorrow' in command_lower or intent.get('DateAdjustmentKeyword') == 'tomorrow':
        request_type = 'forecast'
        period = 'daily'
        forecast_count = 1
        start_offset = 1
        log_info("Detected request for tomorrow's weather")
    elif any(word in command_lower for word in ['forecast', 'next', 'coming']):
        request_type = 'forecast'
        
        # Check for hourly forecast
        if intent.get('TimeUnitKeyword') in ['hour', 'hours', 'hourly'] or 'hourly' in command_lower:
            period = 'hourly'
            forecast_count = 24  # default hourly count
            log_info("Detected hourly forecast request")
        else:
            period = 'daily'
            forecast_count = 5  # default daily count
            log_info("Detected daily forecast request")
        
        # Try to get count from NumberKeyword first
        number_word = intent.get('NumberKeyword')
        if number_word:
            number_map = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            forecast_count = number_map.get(number_word.lower(), forecast_count)
            log_info(f"Found number word: {number_word}, count: {forecast_count}")
        # Then try numeric numbers in the command
        elif numbers := re.findall(r'(\d+)', command_lower):
            forecast_count = min(int(numbers[0]), 24 if period == 'hourly' else 7)
            log_info(f"Found numeric number: {forecast_count}")
    
    # Get weather data based on request type
    if request_type == 'current':
        response = get_weather(location)
        return response
    else:
        response = get_forecast(location, period, forecast_count, start_offset)
        return response

# Create event function
def handle_create_event(command, service):
    if not command:
        success, response = get_user_input("Please specify the event details.")
        if not success:
            return response
        command = response

    # Extract event details from command
    title_match = re.search(r"named\s+(.+?)\s+(at|for|tomorrow|today)", command)
    time_match = re.search(r"\bat\s+([\w\s:]+(?:am|pm)?)", command)
    duration_match = re.search(r"for\s+(\d+|one|two|three|five|ten)\s+(hour|minute|hours|minutes)", command)
    date_match = re.search(r"(tomorrow|today|next\s+\w+)", command)

    # Extract matched details
    event_title = title_match.group(1).strip() if title_match else None
    start_time_str = time_match.group(1).strip() if time_match else None
    duration_str = f"{duration_match.group(1)} {duration_match.group(2)}" if duration_match else None
    event_date = dateparser.parse(date_match.group(0)).date() if date_match else None

    # Get missing information through interaction
    if not event_title:
        success, response = get_user_input("Please provide a title for the event.")
        if not success:
            return response
        event_title = response

    if not start_time_str:
        success, response = get_user_input("At what time should this event start?")
        if not success:
            return response
        start_time_str = response
        
    start_time = dateparser.parse(start_time_str)
    
    if not duration_str:
        success, response = get_user_input(
            "How long will this event last? Provide the duration in hours or minutes.",
            validate_func=lambda x: parse_duration(x, speak_text) is not None
        )
        if not success:
            return response
        duration = parse_duration(response, speak_text)
    else:
        duration = parse_duration(duration_str, speak_text)

    # Create the event if all details are valid
    if event_title and start_time and duration:
        end_time = start_time + timedelta(seconds=duration)
        return add_event(service, event_title, start_time.isoformat(), end_time.isoformat())
    
    return "Event creation failed due to missing or incorrect details."

# Update Event Function (using `datetime`)
def handle_update_event(intent, service):
    try:
        # Initialize variables
        event_name = None
        new_duration = None
        new_start_time = None
        update_params = {
            'new_name': None,
            'new_start_time': None,
            'new_duration': None,
            'new_summary': None
        }

        # Get event name from intent first, then try regex if not found
        event_name = intent.get('EventName')
        if not event_name:
            command = intent.get('utterance', '').lower()
            name_match = re.search(r"named\s+([a-zA-Z0-9\s]+?)(?:\s+to\s+|$)", command)
            if name_match:
                event_name = name_match.group(1).strip()
                log_info(f"Found event name in command: {event_name}")

            # Try to extract duration from initial command
            duration_match = re.search(r"last (\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(hour|hours|minute|minutes)", command)
            if duration_match:
                duration_str = f"{duration_match.group(1)} {duration_match.group(2)}"
                update_params['new_duration'] = parse_duration(duration_str, speak_text)
                log_info(f"Found duration in command: {duration_str}")

        # Only ask for event name if we couldn't extract it
        if not event_name:
            success, event_name = get_user_input("Which event would you like to update?")
            if not success:
                return "Event update canceled."

        # Find the event
        event = find_event_by_title(service, event_name)
        if not event:
            return f"Could not find an event named '{event_name}'"

        # Get current event details
        current_start = datetime.fromisoformat(
            event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00')
        )
        current_end = datetime.fromisoformat(
            event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00')
        )
        current_duration = current_end - current_start
        calendar_timezone = event['start'].get('timeZone', 'UTC')  # Get calendar's timezone

        # Format current duration for display
        duration_mins = int(current_duration.total_seconds() / 60)
        if duration_mins >= 60:
            hours = duration_mins // 60
            mins = duration_mins % 60
            duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
            if mins > 0:
                duration_str += f" and {mins} minute{'s' if mins != 1 else ''}"
        else:
            duration_str = f"{duration_mins} minute{'s' if duration_mins != 1 else ''}"

        speak_text(f"Current event details: {event['summary']}, "
                  f"starting at {current_start.strftime('%I:%M %p')}, "
                  f"duration: {duration_str}")

        # If we have updates from initial command, verify them
        if update_params['new_duration']:
            changes = []
            duration_mins = int(update_params['new_duration'] / 60)
            if duration_mins >= 60:
                hours = duration_mins // 60
                mins = duration_mins % 60
                duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
                if mins > 0:
                    duration_str += f" and {mins} minute{'s' if mins != 1 else ''}"
            else:
                duration_str = f"{duration_mins} minute{'s' if duration_mins != 1 else ''}"
            changes.append(f"duration to {duration_str}")

            verify_msg = f"I'll update the event {', '.join(changes)}. Is this correct?"
            speak_text(verify_msg)
            success, confirmation = get_user_input("Please say yes to confirm or no to cancel.")
            
            if success and confirmation.lower().startswith('y'):
                new_end_time = current_start + timedelta(seconds=update_params['new_duration'])
                return update_event(service, event['id'], updated_end_time=new_end_time.isoformat())
            else:
                return "Event update canceled."

        # If no specific updates were provided in command, ask what to update
        update_options = [
            "Event title",
            "Start time",
            "Duration",
            "Event description"
        ]
            
        speak_text("You may update: " + ", ".join(update_options))
        success, choice = get_user_input("Please pick one.")
            
        if not success:
            return "Event update canceled."
                
        # Initialize update parameters
        update_params = {
            'new_name': None,
            'new_start_time': None,
            'new_duration': None,
            'new_summary': None
        }
                
        # Process the update choice
        if "title" in choice or "name" in choice.lower():
            success, response = get_user_input("What would you like to rename the event to?")
            if success:
                update_params['new_name'] = response
                    
        elif "time" in choice.lower():
            success, response = get_user_input("What time should the event start?")
            if success:
                # Parse time while preserving the original date
                parsed_time, error = parse_time_with_context(response, context={
                    'reference_time': current_start,
                    'preserve_date': True
                })
                if error:
                    return f"Error parsing time: {error}"
                if parsed_time:
                    # Ensure we keep the same date, only update the time
                    new_start = current_start.replace(
                        hour=parsed_time.hour,
                        minute=parsed_time.minute,
                        second=parsed_time.second
                    )
                    # Preserve the original duration
                    new_end = new_start + current_duration
                    update_params['new_start_time'] = new_start.isoformat()
                    update_params['new_end_time'] = new_end.isoformat()

        elif "duration" in choice.lower():
            success, response = get_user_input(
                "How long should the event last? (e.g., 1 hour, 30 minutes)",
                validate_func=lambda x: parse_duration(x, speak_text) is not None
            )
            if success:
                update_params['new_duration'] = parse_duration(response, speak_text)
                    
        elif "description" in choice or "summary" in choice.lower():
            success, response = get_user_input("What should the new event description be?")
            if success:
                update_params['new_summary'] = response

        # Prepare verification message
        changes = []
        if update_params['new_name']:
            changes.append(f"name to '{update_params['new_name']}'")
        if update_params['new_start_time']:
            changes.append(f"start time to {datetime.fromisoformat(update_params['new_start_time']).strftime('%I:%M %p')}")
        if update_params['new_duration']:
            duration_min = int(update_params['new_duration'] / 60)
            if duration_min >= 60:
                hours = duration_min // 60
                mins = duration_min % 60
                duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
                if mins > 0:
                    duration_str += f" and {mins} minute{'s' if mins != 1 else ''}"
            else:
                duration_str = f"{duration_min} minute{'s' if duration_min != 1 else ''}"
            changes.append(f"duration to {duration_str}")
        if update_params['new_summary']:
            changes.append(f"description to '{update_params['new_summary']}'")

        # Verify changes
        if changes:
            verify_msg = f"I'll update the event {', '.join(changes)}. Is this correct?"
            speak_text(verify_msg)
            success, confirmation = get_user_input("Please say yes to confirm or no to cancel.")
            
            if success and confirmation.lower().startswith('y'):
                # Calculate new end time if duration was updated
                if update_params['new_duration']:
                    start_time = update_params['new_start_time'] or current_start
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    new_end_time = start_time + timedelta(seconds=update_params['new_duration'])
                    update_params['new_end_time'] = new_end_time.isoformat()

                # Update the event
                success, message = update_event(
                    service,
                    event['id'],
                    updated_summary=update_params['new_name'],
                    updated_start_time=update_params['new_start_time'],
                    updated_end_time=update_params['new_end_time'],
                    updated_description=update_params['new_summary']
                )
                
                if success:
                    # Format a more detailed success message
                    changes_made = []
                    if update_params['new_start_time']:
                        new_time = datetime.fromisoformat(update_params['new_start_time'])
                        changes_made.append(f"starting at {new_time.strftime('%I:%M %p')}")
                    if update_params['new_duration']:
                        changes_made.append(f"lasting {format_duration(update_params['new_duration'])}")
                    
                    return f"Event updated successfully: {', '.join(changes_made)}"
                return message

            else:
                return "Event update canceled."
        
        return "No changes were specified for the event."

    except Exception as e:
        log_error(f"Error processing event update: {e}")
        return "Failed to update the event due to an error."

# Delete Event Function
def handle_delete_event(intent, service):
    success, event_name = get_user_input("Please provide the event name you want to delete.")
    if not success:
        return "Event deletion canceled."

    events = list_upcoming_events(service)
    event_id = next((event['id'] for event in events if event['summary'].lower() == event_name.lower()), None)

    if event_id:
        return delete_event(service, event_id)
    
    return f"Event '{event_name}' not found."

# Process command
def process_command(command, service):
    """Processes the recognized command and logs parsing details."""
    log_info(f"Processing command: {command}")

    if "exit" in command.lower():
        return "EXIT"

    for intent in engine.determine_intent(command):
        intent_type = intent.get("intent_type")
        log_info(f"Detected intent type: {intent_type}")
        
        # Add the original command to the intent
        intent['command'] = command
        
        if "Weather" in intent_type:
            contextual_recognizer.set_context('weather')
            return handle_get_weather(
                intent=intent,
                recognize_speech_with_cancel_retry=recognize_speech_with_cancel_retry,
                speak_text=speak_text,
                location=None,
                city=intent.get("CityKeyword")
            )
        elif "UpdateEventIntent" in intent_type:
            contextual_recognizer.set_context('event')
            return handle_update_event(intent, service)
        elif "CreateEventIntent" in intent_type:
            contextual_recognizer.set_context('event')
            return handle_create_event(command, service)
        elif "Timer" in intent_type:
            contextual_recognizer.set_context('timer')
            # Pass the speak_text function as an argument
            return set_timer(intent.get("NumberKeyword") + " " + intent.get("DurationUnitKeyword"), speak_text)
        elif "DeleteEventIntent" in intent_type:
            contextual_recognizer.set_context('event')
            return handle_delete_event(intent, service)

    log_error("Failed to match a command to any intent.")
    return "I'm sorry, I couldn't understand the command."