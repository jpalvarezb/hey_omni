from calendar_module import authenticate_google_calendar
from intent_handler import process_command
from speech_module import start_speech_interaction, speak_text, initialize_porcupine
from user_interaction_module import greet_user, recognize_speech_with_cancel_retry
from helpers import log_info, log_error, cleanup_resources

# Main loop to interact with the user
def main():
    log_info("Starting main program...")
    service = None  # Initialize service and porcupine as None
    porcupine = None
    porcupine_cleaned = False  # Track porcupine's cleanup status

    try:
        # Authenticate with Google Calendar and initialize Porcupine for wake word detection
        service = authenticate_google_calendar()
        porcupine = initialize_porcupine()
        log_info("Listening for wake word...")

        while True:
            if start_speech_interaction(porcupine):  # Wait for the wake word
                log_info("Wake word detected!")
                speak_text("Wake word detected!")  # Immediate feedback for wake word

                name = greet_user()  # Ask for the user's name and greet them
                log_info(f"Greeted user: {name}")

                # Continue listening for commands after greeting
                while True:
                    log_info("Listening for a command...")
                    command = recognize_speech_with_cancel_retry()  # Capture user command
                    
                    if command:
                        log_info(f"Command recognized: {command}")

                        # Process command using intent handler
                        response = process_command(command, service, speak_text)
                        log_info(f"Response from process_command: {response}")

                        if response == "EXIT":  # Detect the exit marker
                            log_info("EXIT command received. Cleaning up resources.")
                            porcupine, _, _, porcupine_cleaned = cleanup_resources(porcupine)
                            log_info("Resources cleaned up. Exiting program.")
                            return  # Exit the main loop

                        # Provide feedback to the user if command was recognized but not "EXIT"
                        log_info(f"Responding to user: {response}")
                        speak_text(response)
                    else:
                        log_info("No command recognized, waiting for another command...")

    except Exception as e:
        log_error(f"An error occurred in main loop: {e}")

    finally:
        # Ensure resources are cleaned up on program exit
        if not porcupine_cleaned:
            log_info("Final cleanup of resources.")
            cleanup_resources(porcupine)
        log_info("Program has exited.")

if __name__ == "__main__":
    main()