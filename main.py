from calendar_module import authenticate_google_calendar
from intent_handler import handle_command
from speech_module import start_speech_interaction, speak_text, initialize_porcupine, cleanup_resources
from user_interaction_module import greet_user, recognize_speech

# Main loop to interact with the user
def main():
    print("Starting main program...")
    service = authenticate_google_calendar()  # Authenticate with Google Calendar
    porcupine = initialize_porcupine()  # Initialize Porcupine for wake word detection

    print("Listening for wake word...")
    while True:
        if start_speech_interaction(porcupine):  # Wait for the wake word
            print("Wake word detected!")
            name = greet_user()  # Ask for the user's name and greet them
            print(f"Greeted user: {name}")

            # Continue listening for commands after greeting
            while True:
                print("Listening for a command...")
                command = recognize_speech()  # Vosk Speech-to-Text
                if command:
                    print(f"Command recognized: {command}")
                    if "exit" in command.lower():
                        speak_text(f"Goodbye, {name}!")
                        # Cleanup resources explicitly before exit
                        cleanup_resources(porcupine)
                        return  # Exit the main loop
                    else:
                        response = handle_command(command.lower(), service, speak_text, recognize_speech)
                        print(f"Response: {response}")
                        speak_text(response)
                else:
                    print("No command recognized, waiting for another command...")

if __name__ == "__main__":
    main()