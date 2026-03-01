import cv2
from src.perception.camera import Camera
from src.perception.detector import ObjectDetector
from src.navigation.navigation import target_reached
from src.language.context_llama import LlamaCaptioner
from src.navigation.navigationVLM import StatefulNavigator
from src.audio.stt import Listener
from src.audio.tts import Speaker


def main():
	PROJECT_ID = "lithe-totem-488012-b8"

	camera = Camera()
	detector = ObjectDetector()
	captioner = LlamaCaptioner(PROJECT_ID, location="us-east5")
	listener = Listener()
	speaker = Speaker()

	ret, frame = camera.read()
	if not ret:
		raise RuntimeError("Failed to read initial frame")

	navigator = StatefulNavigator(frame.shape[1], frame.shape[0])

	target_object = None
	navigation_active = False
	last_direction = None

	wake_phrases = [
		"describe",
		"describe the scene",
		"what's in front of me",
		"what is in front of me"
	]

	print("Voice Assistive System Ready")
	speaker.speak("Voice Assistive System Ready")
	print("Say: 'describe the scene' or 'what's in front of me'.")
	speaker.speak("Say describe the scene or what's in front of me.")

	import time
	wake_listen_interval = 0.5
	last_wake_listen = time.time()
	waiting_for_wake = True

	while True:
		ret, frame = camera.read()
		if not ret:
			break

		objects, boxes, frame = detector.detect(frame)

		cv2.imshow("Assistive Vision", frame)
		if cv2.waitKey(1) & 0xFF == 27:
			break

		if not navigation_active:
			if waiting_for_wake:
				now = time.time()
				if now - last_wake_listen > wake_listen_interval:
					heard = listener.listen(prompt=None, timeout=1, phrase_time_limit=2)
					if heard:
						print(f"Wake heard: {heard}")
						if any(phrase in heard for phrase in wake_phrases):
							waiting_for_wake = False
					last_wake_listen = now
				continue

			print("Describing scene...")
			speaker.speak_blocking("Describing scene.")
			description = captioner.describe(frame)
			print(f"\n[LLaMA]: {description}\n")
			speaker.speak_blocking(description)

			while speaker.lock.locked():
				time.sleep(0.05)

			detected_object_names = set([obj.lower() for obj in objects])
			if not detected_object_names:
				print("No objects detected in the scene.")
				speaker.speak("No objects detected in the scene.")
				waiting_for_wake = True
				continue
			print("Objects detected: " + ", ".join(detected_object_names))
			# speaker.speak_blocking("Objects detected: " + ", ".join(detected_object_names))
			while speaker.lock.locked():
				time.sleep(0.05)

			spoken_target = None
			speaker.speak_blocking("Which object should I guide you to? Please say one of: " + ", ".join(detected_object_names))
			while speaker.lock.locked():
				time.sleep(0.05)
			while True:
				cv2.imshow("Assistive Vision", frame)
				if cv2.waitKey(1) & 0xFF == 27:
					camera.release()
					cv2.destroyAllWindows()
					return
				while speaker.lock.locked():
					time.sleep(0.05)
				heard = listener.listen(prompt=None, timeout=2, phrase_time_limit=3)
				print(f"Heard: {heard}")
				if heard:
					heard_clean = heard.strip().lower()
					if heard_clean in detected_object_names:
						print(f"Did you say: '{heard_clean}'? Please say yes or no.")
						speaker.speak_blocking(f"Did you say {heard_clean}? Please say yes or no.")
						while speaker.lock.locked():
							time.sleep(0.05)
						while True:
							cv2.imshow("Assistive Vision", frame)
							if cv2.waitKey(1) & 0xFF == 27:
								camera.release()
								cv2.destroyAllWindows()
								return
							while speaker.lock.locked():
								time.sleep(0.05)
							confirm_voice = listener.listen(prompt=None, timeout=1, phrase_time_limit=2)
							print(f"Confirmation heard: {confirm_voice}")
							if confirm_voice:
								confirm_voice = confirm_voice.strip().lower()
								if 'yes' in confirm_voice:
									spoken_target = heard_clean
									break
								elif 'no' in confirm_voice:
									print("Let's try again.")
									speaker.speak_blocking("Let's try again.")
									break
						if spoken_target:
							break
					else:
						print(f"{heard_clean} is not in the detected objects. Please choose from: {', '.join(detected_object_names)}")
						speaker.speak_blocking(f"{heard_clean} is not in the detected objects. Please choose from: {', '.join(detected_object_names)}")
						while speaker.lock.locked():
							time.sleep(0.05)
				else:
					print("I didn't catch that.")
					speaker.speak_blocking("I didn't catch that.")
					while speaker.lock.locked():
						time.sleep(0.05)

			if spoken_target:
				target_object = spoken_target
				navigation_active = True
				last_direction = None
				print(f"Navigating to: {target_object}")
				speaker.speak(f"Navigating to {target_object}")

		if navigation_active and target_object:
			instruction, lost = navigator.step(target_object, objects, boxes)

			direction = None
			if "Move left" in instruction:
				direction = "left"
			elif "Move right" in instruction:
				direction = "right"
			elif "Go straight" in instruction:
				direction = "straight"
			elif "Stop" in instruction:
				direction = "stop"

			if direction != last_direction:
				print(f"[NAV] {instruction}")
				speaker.speak(instruction)
				last_direction = direction

			if navigator.last_bbox and target_reached(navigator.last_bbox, frame.shape):
				print("Stop. You have reached the object.")
				speaker.speak("Stop. You have reached the object.")
				navigation_active = False
				target_object = None
				navigator.last_bbox = None
				print("Say 'describe the scene' to begin again.")
				speaker.speak("Say describe the scene to begin again.")
				waiting_for_wake = True

	camera.release()
	cv2.destroyAllWindows()

if __name__ == "__main__":
	main()

