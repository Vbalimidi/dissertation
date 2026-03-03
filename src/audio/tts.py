USE_DUSTY = True

import os
import tempfile
import threading
import sys
import time
import socket
import json
if not USE_DUSTY:
    from gtts import gTTS


class Speaker:
    # Approximate speaking rate: ~120 words per minute for NAO robot
    WORDS_PER_SECOND = 120.0 / 60.0  # ~2.0 words/sec

    def __init__(self):
        self.lock = threading.Lock()
        if USE_DUSTY:
            self.sock = None
            self.host = "192.168.1.53" 
            self.port = 12346
            self._connect()

    def _estimate_duration(self, text):
        """Estimate how long the robot takes to speak the text."""
        word_count = len(text.split())
        return max(1.0, word_count / self.WORDS_PER_SECOND + 0.5)

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print("[TTS] Connected to Dusty server")
        except Exception as e:
            print(f"[TTS] Failed to connect to Dusty: {e}")
            self.sock = None

    def speak_blocking(self, text):
        if not text:
            return
        print(f"[TTS] {text}")
        self.lock.acquire()
        try:
            if USE_DUSTY:
                if not self.sock:
                    self._connect()
                if self.sock:
                    try:
                        payload = json.dumps({"say": text})
                        self.sock.sendall(payload.encode("utf-8"))
                        # Wait for robot to finish speaking
                        wait_time = self._estimate_duration(text)
                        print(f"[TTS] Waiting {wait_time:.1f}s for robot to finish speaking")
                        time.sleep(wait_time)
                    except Exception as e:
                        print(f"[TTS] Connection lost: {e}")
                        self.sock = None
            else:
                tts = gTTS(text=text, lang='en')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_path = fp.name
                    tts.save(temp_path)
                os.system(f'afplay "{temp_path}"')
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.lock.release()

    def _play_audio(self, text):
        self.lock.acquire()
        try:
            if USE_DUSTY:
                if not self.sock:
                    self._connect()
                if self.sock:
                    try:
                        payload = json.dumps({"say": text})
                        self.sock.sendall(payload.encode("utf-8"))
                    except Exception as e:
                        print(f"[TTS] Connection lost: {e}")
                        self.sock = None
            else:
                tts = gTTS(text=text, lang='en')
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    temp_path = fp.name
                    tts.save(temp_path)
                os.system(f'afplay "{temp_path}"')
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.lock.release()

    def speak(self, text):
        if not text:
            return
        print(f"[TTS] {text}")
        threading.Thread(target=self._play_audio, args=(text,), daemon=True).start()
