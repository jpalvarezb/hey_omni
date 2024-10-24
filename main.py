from calendar_module import authenticate_google_calendar
from intent_handler import handle_command
from speech_module import recognize_speech, speak_text
from user_interaction_module import greet_user

# Main loop to interact with the user
def main():
    service = authenticate_google_calendar()  # Authenticate with Google Calendar
    name = greet_user()  # Ask for the user's name and greet them
    while True:
        command = recognize_speech()
        if command:
            if "exit" in command.lower():
                speak_text(f"Goodbye, {name}!")
                break
            else:
                # Pass speak_text and recognize_speech into handle_command
                response = handle_command(command.lower(), service, speak_text, recognize_speech)
                print(response)
                speak_text(response)

if __name__ == "__main__":
    main()