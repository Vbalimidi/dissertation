from .navigation import direction_from_box, distance_from_box, navigation_instruction


class StatefulNavigator:
    def __init__(self, frame_width, frame_height, memory_frames=40):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.memory_frames = memory_frames

        self.last_bbox = None
        self.frames_since_seen = 0

    def step(self, target_label, detected_objects, detected_boxes):
        bbox = self._find_target(target_label, detected_objects, detected_boxes)

        if bbox:
            self.last_bbox = bbox
            self.frames_since_seen = 0
            return self._nav_msg(bbox), False

        if self.last_bbox and self.frames_since_seen < self.memory_frames:
            self.frames_since_seen += 1
            return f"[Memory] {self._nav_msg(self.last_bbox)}", False

        return f"Searching for {target_label}...", True

    def _find_target(self, target_label, objects, boxes):
        for obj, box in zip(objects, boxes):
            if target_label in obj.lower():
                return box
        return None

    def _nav_msg(self, bbox):
        direction = direction_from_box(bbox, self.frame_width)
        distance = distance_from_box(bbox, self.frame_height)
        return navigation_instruction(direction, distance)