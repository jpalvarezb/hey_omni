from speech_module import speak_text, recognize_speech_with_cancel_retry

# Function to extract name from user's response
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

# Function to greet the user with a retry limit
def greet_user():
    speak_text("Hey, I'm Omni! What's your name?")
    name = recognize_speech_with_cancel_retry()  # Use the retry mechanism if needed
    if name:
        speak_text(f"Nice to meet you, {name}! How's it going'")
        return name
    else:
        speak_text("Sorry, I didn't catch your name. Can you please repeat?")
        return greet_user()  # Retry if it fails