import google.auth.transport.requests
import cv2
import base64
import time
from openai import OpenAI
from google.auth import default, transport
from src.perception.camera import Camera
from src.perception.detector import ObjectDetector
from src.navigation.navigation import direction_from_box, distance_from_box, navigation_instruction
from src.navigation.target import target_reached

class MaverickCaptioner:
    def __init__(self, project_id, location="us-east5"):
        self.project_id = project_id
        # Get credentials from your gcloud login
        credentials, _ = default()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        # Set up OpenAI client for Google's Maverick endpoint
        self.client = OpenAI(
            base_url=f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi",
            api_key=credentials.token
        )

    def describe(self, frame):
        # Resize image for faster upload (approx 512px)
        resized = cv2.resize(frame, (512, 512))
        _, buffer = cv2.imencode(".jpg", resized)
        b64_image = base64.b64encode(buffer).decode("utf-8")

        try:
            response = self.client.chat.completions.create(
                model="meta/llama-4-maverick-17b-128e-instruct-maas",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the room for a blind person. Focus on floor obstacles."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ]
                }],
                max_tokens=80
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Maverick Error: {str(e)}"

class SystemState:
    IDLE = "idle"
    SCENE_DESCRIPTION = "scene_description"
    TARGET_SELECTION = "target_selection"
    NAVIGATION = "navigation"

def main():
    # --- CONFIGURATION ---
    # Replace with your actual project ID from 'gcloud config get-value project'
    PROJECT_ID = "dissertation-487215" 
    
    camera = Camera()
    detector = ObjectDetector()
    maverick = MaverickCaptioner(PROJECT_ID)

    state = SystemState.IDLE
    target_object = None
    last_nav_instruction = ""

    print("--- System Ready. Press 'd' for description, 'q' to quit ---")

    while True:
        ret, frame = camera.read()
        if not ret: break

        # Always run local YOLO for real-time bounding boxes
        objects, boxes, frame = detector.detect(frame)
        key = cv2.waitKey(1) & 0xFF

        # 1. IDLE: Wait for user to trigger description
        if state == SystemState.IDLE:
            if key == ord("d"):
                state = SystemState.SCENE_DESCRIPTION

        # 2. SCENE DESCRIPTION: Use Llama 4 for high-level understanding
        elif state == SystemState.SCENE_DESCRIPTION:
            print("[System] Capturing scene...")
            caption = maverick.describe(frame)
            print(f"\n[Llama 4 Maverick]: {caption}\n")
            state = SystemState.TARGET_SELECTION

        # 3. TARGET SELECTION: User chooses an object to navigate to
        elif state == SystemState.TARGET_SELECTION:
            target_object = input("Which object should I guide you to? ").lower()
            print(f"Targeting: {target_object}")
            state = SystemState.NAVIGATION

        # 4. NAVIGATION: Local YOLO handles the precise guidance
        elif state == SystemState.NAVIGATION:
            matches = [(obj, box) for obj, box in zip(objects, boxes) if target_object in obj.lower()]

            if not matches:
                instruction = f"Looking for {target_object}..."
            else:
                _, bbox = matches[0]
                dir_ = direction_from_box(bbox, frame.shape[1])
                dist = distance_from_box(bbox, frame.shape[0])
                instruction = navigation_instruction(dir_, dist)

                if target_reached(bbox, frame.shape):
                    instruction = "Stop. You have reached the object."
                    state = SystemState.IDLE
                    target_object = None

            if instruction != last_nav_instruction:
                print(f"[NAV]: {instruction}")
                last_nav_instruction = instruction

        cv2.imshow("Maverick Assistive Vision", frame)
        if key == ord("q"): break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()