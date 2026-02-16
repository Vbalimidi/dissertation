import cv2
from ultralytics import YOLO

class ObjectDetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.5):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        results = self.model(frame, conf=self.conf, verbose=False)
        objects = []
        boxes = []

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            objects.append(label)
            boxes.append((x1, y1, x2, y2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                frame,
                f"{label} {conf:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        return objects, boxes, frame
