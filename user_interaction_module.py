from speech_module import speak_text, recognize_speech_with_cancel_retry
from helpers import log_info

def extract_name(name_response):
    words = name_response.split()
    if "name" in words:
        if "is" in words:
            name_index = words.index("is") + 1
        else:
            name_index = -1  # Assume last word if no "is"
    else:
        name_index = -1
    return words[name_index]

def greet_user():
    speak_text("Hey, I'm Omni! What's your name?")
    name = recognize_speech_with_cancel_retry()  # Use the retry mechanism if needed
    log_info(f"User response captured: {name}")

    if name:
        speak_text(f"How's it going, {name}?")
        log_info(f"Greeted user: {name}")
        return name
    else:
        speak_text("Sorry, I didn't catch your name. Can you please repeat?")
        log_info("Retrying greet_user due to no response.")
        return greet_user()  # Retry if it fails