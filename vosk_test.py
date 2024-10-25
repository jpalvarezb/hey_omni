from speech_module import SpeechRecognizer

def main():
    recognizer = SpeechRecognizer()
    
    # Replace 'test_audio.wav' with the path to your WAV file
    result = recognizer.recognize_from_audio_file('test_audio.wav')
    print("Final result:", result)

if __name__ == "__main__":
    main()