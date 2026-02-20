import google.auth.transport.requests
import cv2
import base64
import time
import threading
import tempfile
import os
import subprocess
from openai import OpenAI
from google.auth import default, transport

from src.perception.camera import Camera
from src.perception.detector import ObjectDetector
from src.navigation.navigation import target_reached
from src.language.context_llama import LlamaCaptioner
from src.navigation.navigationVLM import StatefulNavigator

def main():
    PROJECT_ID = "dissertation-487215"

    camera = Camera()
    detector = ObjectDetector()
    captioner = LlamaCaptioner(PROJECT_ID)

    ret, frame = camera.read()
    if not ret:
        raise RuntimeError("Failed to read initial frame")

    navigator = StatefulNavigator(frame.shape[1], frame.shape[0])

    target_object = None
    last_instruction = ""
    asked_for_target = False

    print("--- System Ready ---")
    print("Press 'd' to describe the scene and select a target.")
    print("Press 'q' to quit.")

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        objects, boxes, frame = detector.detect(frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("d"):
            print("[System] Describing scene...")
            description = captioner.describe(frame)
            print(f"\n[LLaMA]: {description}\n")

            target_object = input("Which object should I guide you to? ").strip().lower()
            asked_for_target = True
            last_instruction = ""

        if asked_for_target and target_object:
            instruction, lost = navigator.step(target_object, objects, boxes)

            if lost:
                if navigator.frames_since_seen % 60 == 0:
                    prompt = (
                        f"I am looking for a {target_object}. "
                        "Is it on the left, center, or right?"
                    )
                    hint = captioner.describe(frame, prompt)
                    instruction = f"[VLM Hint] {hint}"

            if navigator.last_bbox and target_reached(navigator.last_bbox, frame.shape):
                instruction = "Stop. You have reached the object."
                target_object = None
                asked_for_target = False
                navigator.last_bbox = None

            if instruction != last_instruction:
                print(f"[NAV] {instruction}")
                last_instruction = instruction

        cv2.imshow("Assistive Vision", frame)

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()