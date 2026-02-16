import cv2
from .navigation import direction_from_box, distance_from_box, navigation_instruction

class StatefulNavigator:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.last_valid_bbox = None
        self.frames_since_seen = 0
        self.max_memory_frames = 40 
        self.vlm_recovery_mode = False

    def process_frame(self, target_label, detected_objects, detected_boxes):
        matches = [box for obj, box in zip(detected_objects, detected_boxes) if target_label in obj.lower()]
        
        if matches:
            self.last_valid_bbox = matches[0]
            self.frames_since_seen = 0
            self.vlm_recovery_mode = False
            return self._create_nav_msg(self.last_valid_bbox), False

        if self.last_valid_bbox is not None and self.frames_since_seen < self.max_memory_frames:
            self.frames_since_seen += 1
            return f"[Memory] {self._create_nav_msg(self.last_valid_bbox)}", False

        self.vlm_recovery_mode = True
        return f"Lost sight of {target_label}. Re-scanning with VLM...", True

    def _create_nav_msg(self, bbox):
        dir_ = direction_from_box(bbox, self.frame_width)
        dist = distance_from_box(bbox, self.frame_height)
        return navigation_instruction(dir_, dist)