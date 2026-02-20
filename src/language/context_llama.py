import base64
import cv2
import openai
from google.auth import default, transport

class LlamaCaptioner:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        
        credentials, _ = default()
        auth_request = transport.requests.Request()
        credentials.refresh(auth_request)

        self.client = openai.OpenAI(
            base_url=f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi",
            api_key=credentials.token
        )

    def describe(self, frame, custom_prompt=None):
        prompt = custom_prompt or "Describe the scene in detail, including objects, their relationships, and any notable features."
        
        imageb64 = self.encode_frame(frame)

        response = self.client.chat.completions.create(
            model="meta/llama-4-maverick-17b-128e-instruct-maas",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{imageb64}"
                        }
                    }
                ]
            }],
            max_tokens=150
        )

        return response.choices[0].message.content

    @staticmethod
    def _encode_frame(frame):
        frame = cv2.resize(frame, (512, 512))
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")