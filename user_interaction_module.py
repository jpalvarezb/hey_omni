from speech_module import speak_text, recognize_speech

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
def greet_user(max_retries=3):
    attempts = 0
    while attempts < max_retries:
        speak_text("Hello, I'm Omni! What's your name?")
        name_response = recognize_speech()
        if name_response:
            name = extract_name(name_response)
            speak_text(f"Hello {name}, how can I assist you today?")
            return name
        else:
            speak_text("Sorry, I didn't catch your name. Can you please repeat?")
            attempts += 1

    speak_text("Sorry, I still couldn't catch your name. Let's proceed without it.")
    return None  # Return None if the name couldn't be captured after retries