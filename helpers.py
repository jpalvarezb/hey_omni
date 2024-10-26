import logging
from datetime import datetime
from word2number import w2n

logging.basicConfig(level=logging.INFO)

# Utility logging functions
def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

# Parsing Function
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

# Utility to format datetime to a user-friendly string
def format_datetime_to_user_friendly(dt):
    return datetime.fromisoformat(dt).strftime('%I:%M %p on %A, %B %d')