# duration_test.py
import logging
from word2number import w2n

# Set up logging to display all info and error messages
logging.basicConfig(level=logging.INFO)

# Simulate a speech output function
def speak_text(text):
    print(f"SPEECH OUTPUT: {text}")

# Parsing function
def parse_duration(duration_str, speak_text):
    try:
        # Check for empty input
        if not duration_str:
            raise ValueError("No duration provided.")

        # Split duration string and validate format
        words = duration_str.strip().lower().split()
        if len(words) < 2:
            raise ValueError("Specify both a number and a unit, like '10 seconds'.")

        # Extract number and unit
        number_part = " ".join(words[:-1])  # All but last word
        unit_part = words[-1]  # Last word as unit

        # Convert words to a number
        value = w2n.word_to_num(number_part)

        # Map units to seconds
        units = {"second": 1, "seconds": 1, "minute": 60, "minutes": 60, "hour": 3600, "hours": 3600}
        if unit_part not in units:
            raise ValueError(f"Unrecognized unit '{unit_part}'.")

        return value * units[unit_part]

    except ValueError as e:
        logging.error(f"Failed to parse duration '{duration_str}': {e}")
        speak_text("Please specify a number and a unit, like '10 seconds' or '5 minutes'.")
        return None

# Testing parse_duration with different inputs
test_inputs = ["ten seconds", "5 minutes", "set a timer", "10 hours"]
for input_str in test_inputs:
    print(f"\nTesting input: '{input_str}'")
    result = parse_duration(input_str, speak_text)
    print(f"Parsed Result: {result if result is not None else 'Parsing failed'}")