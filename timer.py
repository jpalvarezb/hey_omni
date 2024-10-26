import time
import threading
from helpers import parse_duration

def countdown_timer(duration, speak_text):
    """Handles the countdown and notifies when the timer ends."""
    time.sleep(duration)
    speak_text("Time's up!")

def set_timer(duration_str, speak_text):
    """Sets a timer for the specified duration without blocking the main program."""
    duration = parse_duration(duration_str, speak_text)
    if duration is not None:
        speak_text(f"Setting a timer for {duration_str}.")
        # Start the timer in a separate thread
        timer_thread = threading.Thread(target=countdown_timer, args=(duration, speak_text))
        timer_thread.start()
    else:
        # parse_duration handles errors, so we simply pass if duration is None
        pass