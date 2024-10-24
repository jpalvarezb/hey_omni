import speech_recognition as sr
import pyttsx3

# Initialize recognizer and speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Function to convert text to speech
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Function to recognize speech
def recognize_speech():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.energy_threshold = 300  # Adjust sensitivity to background noise
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            # Attempt to recognize speech
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            speak_text("Sorry, I did not understand that. Please repeat.")
            return ""  # Return an empty string if speech was not understood
        except sr.RequestError:
            print("Error with the speech recognition service.")
            speak_text("There was a problem with the speech service. Please try again.")
            return None  # Return None if there's an issue with the service

# Optional retry mechanism if speech isn't recognized the first time
def recognize_speech_with_retry(attempts=3):
    for _ in range(attempts):
        result = recognize_speech()
        if result:  # If a valid result is returned, exit the loop
            return result
        speak_text("Let me try that again.")
    speak_text("Sorry, I couldn't understand you after several attempts.")
    return None  # Return None after exceeding the retry attempts