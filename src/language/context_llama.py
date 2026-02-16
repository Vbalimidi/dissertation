import base64
import cv2
import openai
from google.auth import default, transport

class LlamaServerlessCaptioner:
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

    def describe(self, frame):
        _, buffer = cv2.imencode(".jpg", frame)
        base64_image = base64.b64encode(buffer).decode("utf-8")

        try:
            response = self.client.chat.completions.create(
                model="llama-4-maverick-17b-128e-instruct-maas",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this scene for a blind person in one clear sentence. Mention objects and their positions."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                max_tokens=150
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Cloud API Error: {str(e)}"