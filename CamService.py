import numpy as np
from kafka import KafkaProducer
import json
import time

import os
import sys
import cv2
import time
import torch
import utils
import argparse
import traceback
import numpy as np

from PIL import Image
from models import gazenet
from mtcnn import FaceDetector
import matplotlib.pyplot as plt
from Arduino_control.ArduinoServoControl import *

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


# print('Running Camera Service')
#
# for i in range(600):
#
#     kids = np.random.randint(1, 10)
#     # attention = np.random.randint(0, 100)
#     attention = 50 + 50 * np.sin(float(time.time()))
#     producer.send('camera', value={'attention': str(attention), 'kids': str(kids)}, key='CamService')
#     time.sleep(2)



parser = argparse.ArgumentParser()
parser.add_argument('--cpu', action='store_true')
parser.add_argument('--weights', '-w', type=str, default='models/weights/gazenet.pth')
args = parser.parse_args()

# print('Loading MobileFaceGaze model...')
device = torch.device("cuda:0" if (torch.cuda.is_available() and not args.cpu) else "cpu")
model = gazenet.GazeNet(device)

if(not torch.cuda.is_available() and not args.cpu):
    print('Tried to load GPU but found none. Please check your environment')

state_dict = torch.load(args.weights, map_location=device)
model.load_state_dict(state_dict)
print('Model loaded using {} as device'.format(device))

print('Running Camera Service')

model.eval()

fps = 0
frame_num = 0
frame_samples = 6
fps_timer = time.time()
# cap = cv2.VideoCapture(2)
cap = cv2.VideoCapture(0)

face_detector = FaceDetector(device=device)
fig = plt.figure(0)
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

x_angle = 0
y_angle = 0
max_angle = 180
producer_frames = 0
attention_avg = 0
kids_avg = 0

while True:
    plt.close()
    try:
        ret, frame = cap.read()
        frame = frame[:, :, ::-1]
        frame = cv2.flip(frame, 1)
        img_h, img_w, _ = np.shape(frame)
        frame_num += 1
        # Detect Faces
        display = frame.copy()
        faces, landmarks = face_detector.detect(Image.fromarray(frame))
        kids = 0
        attention = 0
        if len(faces) != 0:
            for f, lm in zip(faces, landmarks):
                # Confidence check
                if(f[-1] > 0.98):
                    # Crop and normalize face Face
                    face, gaze_origin, M = utils.normalize_face(lm, frame)
                    kids += 1
                    # Predict gaze
                    with torch.no_grad():
                        gaze = model.get_gaze(face)
                        gaze = gaze[0].data.cpu()

                    # Draw results
                    display = cv2.circle(display, gaze_origin, 3, (0, 255, 0), -1)
                    display = utils.draw_gaze(display, gaze_origin, gaze, color=(255, 0, 0), thickness=2)

                    # xs.append(dt.datetime.now().strftime('%H:%M:%S.%f'))
                    xs.append(time.time())
                    ys.append(utils.attention(gaze))
                    # utils.live_plot(xs, ys, plotWidget)

                    x_face_origin = int(gaze_origin[0])
                    y_face_origin = int(gaze_origin[1])
                    x_angle += 1 if x_face_origin > 300 else -1
                    y_angle += 1 if y_face_origin > 300 else -1
                    # print(x_face_origin)

                    attention += abs(int(100 * np.sin(gaze[1])))

        # Calc FPS
        if (frame_num == frame_samples):
            fps = time.time() - fps_timer
            fps = frame_samples / fps
            fps_timer = time.time()
            frame_num = 0
        display = cv2.putText(display, 'FPS: {:.2f}'.format(fps), (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 1, cv2.LINE_AA)

        # plot
        cv2.imshow('Gaze Demo', cv2.cvtColor(display, cv2.COLOR_RGB2BGR))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            cap.release()
            break
        if kids > 0:
            attention /= kids
        # Producer

        if producer_frames == 5:
            attention_avg /= 5
            attention_avg = 100 - attention_avg
            kids_avg /= 5
            producer.send('camera', value={'attention': str(attention_avg), 'kids': str(kids_avg)}, key='CamService')
            producer.send('servos', value={'dx': str(10), 'dy': str(10)}, key='CamService')
            producer_frames = 0
            attention_avg = 0
            kids_avg = 0
        else:
            attention_avg += attention
            kids_avg += kids
            producer_frames += 1

    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        cap.release()
        cv2.destroyAllWindows()
        traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
        break

cap.release()
cv2.destroyAllWindows()

