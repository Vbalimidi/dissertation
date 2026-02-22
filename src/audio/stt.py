import speech_recognition as sr

class Listener:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.last_command = None

        with self.microphone as source:
            print("[STT] Calibrating for background noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
    def _callback(self, recognizer, audio):
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"[STT] Heard: {command}")
            self.last_command = command
        except sr.UnknownValueError:
            pass 
        except sr.RequestError:
            print("[STT] API Error - check internet connection")

    def start_listening(self):
        return self.recognizer.listen_in_background(self.microphone, self._callback)

listener = Listener()