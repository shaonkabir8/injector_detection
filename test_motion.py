import sys
import os
import cv2
import numpy as np

# Ensure the detector directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.motion_detector import global_motion_detector

def run_test():
    print("[test] Starting motion detector test...")
    
    # Create two frames: one black, one with a white box to simulate motion
    frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
    frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame2, (100, 100), (200, 200), (255, 255, 255), -1)
    
    # Pass first frame (establishes background)
    print("[test] Frame 1 (black background)")
    has_motion, score, meta = global_motion_detector.detect("test_cam", frame1)
    print(f"Motion: {has_motion}, Score: {score}, Meta: {meta}")
    
    # Pass second frame (different, should trigger motion)
    print("[test] Frame 2 (white square)")
    has_motion, score, meta = global_motion_detector.detect("test_cam", frame2)
    print(f"Motion: {has_motion}, Score: {score}, Meta: {meta}")

if __name__ == "__main__":
    run_test()
