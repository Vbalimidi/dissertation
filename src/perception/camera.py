import cv2

class Camera:
    def __init__(self, cam_id=1):
        self.cap = cv2.VideoCapture(cam_id)

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()