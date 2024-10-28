import logging
from datetime import datetime
from word2number import w2n

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

def parse_city(command):
    if not command:
        return None

    exclude_words = [
        'in', 'at', 'for', 'the', 'weather', 'forecast', 'what', 'is', 'whats', 
        "what's", 'city', 'town', 'climate', 'like', 'going', 'to', 'be', 'current',
        'please', 'tell', 'me', 'about', 'check', 'get', 'want', 'know'
    ]

    try:
        # Extract text following "in" if it exists
        if ' in ' in command.lower():
            location = command.lower().split(' in ')[-1]
        else:
            location = command

        # Clean up the location string
        words = location.strip().lower().split()
        
        # Filter out excluded words
        filtered_words = [word for word in words if word.lower() not in exclude_words]
        
        # Handle multi-word cities
        i = 0
        cleaned_words = []
        while i < len(filtered_words):
            current_word = filtered_words[i].lower()
            if i < len(filtered_words) - 1 and current_word in ['san', 'new', 'los', 'las']:
                # Combine multi-word city names
                cleaned_words.append(f"{filtered_words[i]} {filtered_words[i+1]}")
                i += 2
            else:
                cleaned_words.append(filtered_words[i])
                i += 1

        # Return None if no valid words remain
        if not cleaned_words:
            return None
            
        city_name = ' '.join(cleaned_words).title()
        log_info(f"Parsed city name: {city_name}")
        return city_name

    except Exception as e:
        log_error(f"Error parsing city name: {e}")
        return None

# Utility to format datetime to a user-friendly string
def format_datetime_to_user_friendly(dt):
    return datetime.fromisoformat(dt).strftime('%I:%M %p on %A, %B %d')
