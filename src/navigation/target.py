def target_reached(box, frame_shape, threshold=0.25):
    x1, y1, x2, y2 = box
    box_area = (x2 - x1) * (y2 - y1)
    frame_area = frame_shape[0] * frame_shape[1]
    return (box_area / frame_area) > threshold

