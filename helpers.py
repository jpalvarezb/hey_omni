import logging
from datetime import datetime, timedelta
from word2number import w2n
from zoneinfo import ZoneInfo
import dateparser

logging.basicConfig(level=logging.INFO)

# Utility logging functions
def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

# Cleanup Resources with status tracking
def cleanup_resources(porcupine, recognizer=None, stream=None, porcupine_cleaned=False):
    """Cleans up resources, avoiding double-freeing errors."""
    if porcupine and not porcupine_cleaned:
        log_info("Cleaning up Porcupine resources...")
        porcupine.delete()
        porcupine_cleaned = True  # Mark as cleaned up

    if stream:
        log_info("Stopping and closing audio stream...")
        stream.stop_stream()
        stream.close()

    if recognizer:
        log_info("Terminating PyAudio instance...")
        recognizer.terminate()

    log_info("Resources cleaned up.")
    return porcupine, recognizer, stream, porcupine_cleaned

# Parsing Functions
def parse_duration(duration_str, speak_text):
    try:
        if not duration_str:
            raise ValueError("No duration provided.")

        words = duration_str.strip().lower().split()
        log_info(f"Split input words: {words}")

        # Check that we have at least a number and a unit
        if len(words) < 2:
            raise ValueError("Insufficient information. Please specify both a number and a unit, like '10 seconds'.")

        number_part = " ".join(words[:-1])  # Everything but the last word
        unit_part = words[-1]  # Last word as unit

        # Attempt to parse the number
        try:
            value = w2n.word_to_num(number_part)
        except ValueError:
            raise ValueError(f"Could not parse '{number_part}' as a number.")

        # Validate and interpret the unit
        units = {"second": 1, "seconds": 1, "minute": 60, "minutes": 60, "hour": 3600, "hours": 3600}
        if unit_part not in units:
            raise ValueError(f"Unrecognized unit '{unit_part}'. Expected 'seconds', 'minutes', or 'hours'.")

        duration_seconds = value * units[unit_part]
        log_info(f"Parsed duration in seconds: {duration_seconds}")
        return duration_seconds

    except ValueError as e:
        log_error(f"Failed to parse duration '{duration_str}': {e}")
        speak_text("I'm sorry, I couldn't understand the timer duration. Please specify a number and a unit, like '10 seconds' or '5 minutes'.")
        return None

def parse_city(text, remove_time_words=False):
    if not text:
        return None
        
    # Words to remove before parsing city
    time_related_words = {
        'weather', 'forecast', 'temperature', 'climate',
        'next', 'coming', 'following',
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'day', 'days', 'hour', 'hours', 'hourly',
        'in', 'at', 'for', 'the', 'whats', "what's", 'like'
    }
    
    # Clean up the text
    text = text.strip().lower()
    
    # Remove time-related words if requested
    if remove_time_words:
        words = text.split()
        words = [word for word in words if word not in time_related_words]
        text = ' '.join(words)
    
    log_info(f"Parsing city from cleaned text: {text}")
    
    # Try to find known city names
    known_cities = {
        'new york': 'New York',
        'paris': 'Paris',
        'london': 'London',
        'tokyo': 'Tokyo',
        'miami': 'Miami',
        'managua': 'Managua'
    }
    
    # Check for exact matches first (case insensitive)
    text_lower = text.lower()
    for city_lower, city_proper in known_cities.items():
        if city_lower in text_lower:
            log_info(f"Found known city: {city_proper}")
            return city_proper
            
    # If no exact match, try to find the first capitalized word
    original_words = text.split()  # Use original text to preserve capitalization
    for word in original_words:
        if word.istitle() and word.lower() not in time_related_words:
            log_info(f"Found capitalized city name: {word}")
            return word
            
    log_info("No city name found in text")
    return None

# Utility to format datetime to a user-friendly string
def format_datetime_to_user_friendly(dt):
    return datetime.fromisoformat(dt).strftime('%I:%M %p on %A, %B %d')

def get_local_timezone():
    """Get the system's local timezone."""
    try:
        return ZoneInfo('America/Los_Angeles')  # Default to PT
    except Exception as e:
        log_error(f"Error getting local timezone: {e}")
        return ZoneInfo('UTC')  # Fallback to UTC using ZoneInfo

def ensure_timezone_aware(dt, timezone=None):
    """Ensure a datetime object is timezone-aware."""
    if timezone is None:
        timezone = get_local_timezone()
        
    if dt.tzinfo is None:
        # Replace localize with replace(tzinfo=)
        return dt.replace(tzinfo=timezone)
    return dt

def parse_time_with_context(time_str, context=None):
    """Parse time string with improved context handling."""
    try:
        if isinstance(time_str, datetime):
            return time_str, None
            
        context = context or {}
        reference_time = context.get('reference_time', datetime.now())
        preserve_date = context.get('preserve_date', False)

        # Handle basic number input (e.g., "six")
        if isinstance(time_str, str) and time_str.replace(' ', '').isalpha():
            try:
                hour = w2n.word_to_num(time_str)
                if 1 <= hour <= 12:
                    current_hour = reference_time.hour
                    meridian = "PM" if current_hour >= 12 or hour < 7 else "AM"
                    time_str = f"{hour} {meridian}"
            except ValueError:
                pass

        # Parse the time string using the reference time
        parsed_time = dateparser.parse(
            time_str,
            settings={
                'RELATIVE_BASE': reference_time,
                'PREFER_DATES_FROM': 'current_period'
            }
        )
        
        if not parsed_time:
            return None, "Could not understand the time format"

        # If preserving date, use the reference date with new time
        if preserve_date:
            parsed_time = parsed_time.replace(
                year=reference_time.year,
                month=reference_time.month,
                day=reference_time.day
            )

        return parsed_time, None

    except Exception as e:
        log_error(f"Error parsing time: {e}")
        return None, str(e)

def format_duration(seconds):
    """Convert seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

def calculate_event_duration(start_time, end_time):
    """Calculate duration between two datetime objects."""
    if not all([start_time, end_time]):
        return None
        
    try:
        # Ensure both times are timezone aware
        start_time = ensure_timezone_aware(start_time)
        end_time = ensure_timezone_aware(end_time)
        
        duration = end_time - start_time
        return int(duration.total_seconds())
    except Exception as e:
        log_error(f"Error calculating duration: {e}")
        return None

def format_datetime_to_user_friendly(dt):
    """Enhanced datetime formatting with timezone handling."""
    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        
        dt = ensure_timezone_aware(dt)
        return dt.strftime('%I:%M %p on %A, %B %d')
    except Exception as e:
        log_error(f"Error formatting datetime: {e}")
        return str(dt)

def format_duration(seconds):
    """Convert seconds to human-readable duration string."""
    minutes = int(seconds / 60)
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
        if mins > 0:
            duration_str += f" and {mins} minute{'s' if mins != 1 else ''}"
    else:
        duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
    return duration_str