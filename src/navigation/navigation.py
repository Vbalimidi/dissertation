def direction_from_box(box, frame_width):
    x_center = (box[0] + box[2]) / 2
    left_boundary = frame_width / 3
    right_boundary = 2 * frame_width / 3
    if x_center < left_boundary:
        return "left"
    elif x_center > right_boundary:
        return "right"
    else:
        return "straight"

def distance_from_box(box, frame_height):
    box_height = box[3] - box[1]
    ratio = box_height / frame_height
    if ratio > 0.45:
        return "very close"
    elif ratio > 0.3:
        return "close"
    elif ratio > 0.15:
        return "a few steps away"
    else:
        return "far"

def navigation_instruction(direction, distance):
    if distance == "very close":
        return "Stop. The object is directly in front of you."
    if direction == "left":
        return f"Move left. The object is {distance}."
    elif direction == "right":
        return f"Move right. The object is {distance}."
    else:
        return f"Go straight. The object is {distance}."

def target_reached(box, frame_shape, threshold=0.25):
    x1, y1, x2, y2 = box
    box_area = (x2 - x1) * (y2 - y1)
    frame_area = frame_shape[0] * frame_shape[1]
    return (box_area / frame_area) > threshold
