
import cv2
import numpy as np

# Test 1: Can we read frames?
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
ret, frame = cap.read()
print(f'0. Frame capture: {ret}')
if ret:
    print(f'   Shape: {frame.shape}')

# Test 2: Can we write a simple video?
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('videostore/testvideos/test_opencv.mp4', fourcc, 30, (640, 480))
#out = cv2.VideoWriter('test_opencv.mp4', fourcc, 30, (640, 480))
for i in range(90):  # 3 seconds
    ret, frame = cap.read()
    if ret:
        out.write(frame)
out.release()
cap.release()
print('2. OpenCV test video created: test_opencv.mp4')
print('   Try playing this file!')
