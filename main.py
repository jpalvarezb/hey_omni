from calendar_module import authenticate_google_calendar
from intent_handler import handle_command
from speech_module import start_speech_interaction, speak_text
from user_interaction_module import greet_user

# Main loop to interact with the user using wake word detection and voice commands
def main():
    service = authenticate_google_calendar()  # Authenticate with Google Calendar
    name = greet_user()  # Ask for the user's name and greet them

    while True:
        # Listen for wake word, then process speech commands
        start_speech_interaction()

        command = start_speech_interaction()  # Wait for wake word and recognize command
        if command:
            if "exit" in command.lower():
                speak_text(f"Goodbye, {name}!")
                break
            else:
                # Pass speak_text and the recognized speech command to handle_command
                response = handle_command(command.lower(), service, speak_text, start_speech_interaction)
                print(response)
                speak_text(response)

if __name__ == "__main__":
    main()