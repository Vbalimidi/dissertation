from gtts import gTTS
import tempfile
import os
import threading
import subprocess

class Speaker:
    def __init__(self):
        self.lock = threading.Lock()

    def _speak(self, text):
        with self.lock:
            tts = gTTS(text=text, lang="en", slow=False)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                path = f.name
                tts.save(path)

            subprocess.run(
                ["afplay", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            os.remove(path)

    def say(self, text):
        if text:
            threading.Thread(
                target=self._speak,
                args=(text,),
                daemon=True
            ).start()
