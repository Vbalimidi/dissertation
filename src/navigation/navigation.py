# src/navigation/navigator.py
def direction_from_box(box, frame_width):
    x_center = (box[0] + box[2]) / 2
    ratio = x_center / frame_width
    if ratio < 0.33:
        return "left"
    elif ratio > 0.66:
        return "right"
    return "ahead"

def distance_from_box(box, frame_height):
    box_height = box[3] - box[1]
    ratio = box_height / frame_height
    if ratio > 0.45:
        return "very close"
    if ratio > 0.3:
        return "close"
    if ratio > 0.15:
        return "a few steps away"
    return "far"

def navigation_instruction(direction, distance):
    if distance == "very close":
        return "Stop. The object is right in front of you. Reach forward."
    if direction == "left":
        return f"Turn slightly left. The object is {distance}."
    if direction == "right":
        return f"Turn slightly right. The object is {distance}."
    return f"Walk forward. The object is {distance}."
