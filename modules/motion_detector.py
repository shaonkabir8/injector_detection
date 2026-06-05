import cv2
import numpy as np
from typing import Dict, Tuple

class MotionDetector:
    """
    Stateful motion detector for video streams.
    Implements background subtraction (MOG2) to detect significant frame changes.
    """
    def __init__(self, min_area: int = 500, var_threshold: int = 16, history: int = 500):
        self.min_area = min_area
        self.bg_subtractors: Dict[str, cv2.BackgroundSubtractor] = {}
        self.var_threshold = var_threshold
        self.history = history

    def detect(self, source_id: str, frame: np.ndarray) -> Tuple[bool, float, dict]:
        """
        Detect motion in a given frame for a specific source.
        Returns:
            motion_detected: bool
            motion_score: float (max contour area)
            metadata: dict (bounding boxes of motion)
        """
        if source_id not in self.bg_subtractors:
            self.bg_subtractors[source_id] = cv2.createBackgroundSubtractorMOG2(
                history=self.history, 
                varThreshold=self.var_threshold, 
                detectShadows=True
            )
            
        bg_sub = self.bg_subtractors[source_id]
        
        # Resize for faster processing if needed, but we'll use original to keep bbox coords matching
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        fg_mask = bg_sub.apply(blurred)
        
        # Threshold to remove shadows (which MOG2 marks as gray/127)
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_area = 0.0
        motion_detected = False
        bboxes = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                motion_detected = True
                if area > max_area:
                    max_area = area
                x, y, w, h = cv2.boundingRect(contour)
                bboxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "area": float(area)})
                
        metadata = {
            "motion_score": max_area,
            "motion_zones": bboxes
        }
        
        return motion_detected, max_area, metadata

# Global instance for shared state across API calls
global_motion_detector = MotionDetector(min_area=1000)
