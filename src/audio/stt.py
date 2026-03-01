import speech_recognition as sr
class Listener:
	def __init__(self):
		self.recognizer = sr.Recognizer()
		self.microphone = sr.Microphone()

	def listen(self, prompt=None, timeout=3, phrase_time_limit=4):
		if prompt:
			print(prompt)
		with self.microphone as source:
			self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
			try:
				audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
				text = self.recognizer.recognize_google(audio)
				return text.lower()
			except (sr.WaitTimeoutError, sr.UnknownValueError):
				return None
			except sr.RequestError:
				print("[STT] API connection error")
				return None
            