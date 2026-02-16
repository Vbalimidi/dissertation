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

class LlamaCaptioner:
    def __init__(self, project_id, location="us-east5"):
        self.project_id = project_id
        credentials, _ = default()
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)

        self.client = OpenAI(
            base_url=f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi",
            api_key=credentials.token
        )

    def describe(self, frame, custom_prompt=None):
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
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Maverick Error: {str(e)}"
        
class StatefulNavigator:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.last_valid_bbox = None
        self.frames_since_seen = 0
        self.max_memory_frames = 30 
        self.vlm_recovery_attempts = 0

    def get_instruction(self, target_obj, objects, boxes):
        matches = [box for obj, box in zip(objects, boxes) if target_obj in obj.lower()]
        
        if matches:
            self.last_valid_bbox = matches[0]
            self.frames_since_seen = 0
            self.vlm_recovery_attempts = 0 
            return self._gen_msg(self.last_valid_bbox), False

        if self.last_valid_bbox is not None and self.frames_since_seen < self.max_memory_frames:
            self.frames_since_seen += 1
            return f"[Memory] {self._gen_msg(self.last_valid_bbox)}", False

        return f"Searching for {target_obj}...", True

    def _gen_msg(self, bbox):
        dir_ = direction_from_box(bbox, self.frame_width)
        dist = distance_from_box(bbox, self.frame_height)
        return navigation_instruction(dir_, dist)

class SystemState:
    IDLE = "idle"
    SCENE_DESCRIPTION = "scene_description"
    TARGET_SELECTION = "target_selection"
    NAVIGATION = "navigation"

def main():
    PROJECT_ID = "dissertation-487215" 
    
    camera = Camera()
    detector = ObjectDetector()
    Llama = LlamaCaptioner(PROJECT_ID)

    ret, init_frame = camera.read()
    nav_logic = StatefulNavigator(init_frame.shape[1], init_frame.shape[0])

    state = SystemState.IDLE
    target_object = None
    last_nav_instruction = ""

    print("--- System Ready. Press 'd' for description, 'q' to quit ---")

    while True:
        ret, frame = camera.read()
        if not ret: break

        objects, boxes, frame = detector.detect(frame)
        key = cv2.waitKey(1) & 0xFF

        if state == SystemState.IDLE:
            if key == ord("d"):
                state = SystemState.SCENE_DESCRIPTION

        elif state == SystemState.SCENE_DESCRIPTION:
            print("[System] Capturing scene...")
            caption = Llama.describe(frame)
            print(f"\n[Llama 4]: {caption}\n")
            state = SystemState.TARGET_SELECTION

        elif state == SystemState.TARGET_SELECTION:
            target_object = input("Which object should I guide you to? ").lower()
            print(f"Targeting: {target_object}")
            state = SystemState.NAVIGATION

        elif state == SystemState.NAVIGATION:
            instruction, lost_too_long = nav_logic.get_instruction(target_object, objects, boxes)

            if lost_too_long:
                if nav_logic.vlm_recovery_attempts % 60 == 0:
                    print(f"[System] YOLO lost {target_object}. Asking VLM for help...")
                    prompt = f"I am looking for a {target_object}. Is it in the center, left, or right of the image?"
                    vlm_hint = Llama.describe(frame, custom_prompt=prompt)
                    instruction = f"[VLM Hint]: {vlm_hint}"
                nav_logic.vlm_recovery_attempts += 1

            if nav_logic.last_valid_bbox and target_reached(nav_logic.last_valid_bbox, frame.shape):
                instruction = "Stop. You have reached the object."
                state = SystemState.IDLE
                target_object = None
                nav_logic.last_valid_bbox = None

            if instruction != last_nav_instruction:
                print(f"[NAV]: {instruction}")
                last_nav_instruction = instruction

        cv2.imshow("Maverick Assistive Vision", frame)
        if key == ord("q"): break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()