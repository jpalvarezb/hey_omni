import time
from helpers import parse_duration

def set_timer(duration_str, speak_text):
    """Sets a timer for the specified duration."""
    duration = parse_duration(duration_str, speak_text)
    if duration is not None:
        speak_text(f"Setting a timer for {duration_str}.")
        time.sleep(duration)
        speak_text("Time's up!")
    else:
        # No need to handle the error here as it's already managed in parse_duration
        pass