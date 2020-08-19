import os
import sys
import cv2
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
from datetime import datetime
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *

enable_print = False
# ------ Init RabbitMQ --------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('cam_service')
rabbitMQ.declare_exchanges(['main'])

# Setup to listen to messages with key "video.action" - currently only service publishing on this is StoryTeller
# rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'video.action', 'callback': callback})
# rabbitMQ.setup_queues()
# rabbitMQ.start_consume()

'''
# TO SEND METRICS DO:
message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'n_kids': n_faces, 'attention': attention_metric}

rabbitMQ.publish(exchange='main',
                 routing_key='camera',    # routing key could also be: camera.servo if sending direct angles
                 body=message)


'''
# ------ Read runtime args --------------------------------------------------------------------------------------------


def gaze_detection(args):
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
    cap = cv2.VideoCapture(args.camera)
    # cap = cv2.VideoCapture(0)

    face_detector = FaceDetector(device=device)
    fig = plt.figure(0)
    ax = fig.add_subplot(1, 1, 1)
    xs = []
    ys = []

    roll = 50
    pitch = 50
    avg_roll = 0
    avg_pitch = 0
    max_angle = 180
    producer_frames = 0
    attention_avg = 0
    kids_avg = 0
    x_face_origin = 0
    y_face_origin = 0

    while True:
        plt.close()
        try:
            ret, frame = cap.read()
            frame = frame[:, :, ::-1]
            # frame = cv2.flip(frame, 1)
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            img_h, img_w, _ = np.shape(frame)
            frame_num += 1
            # Detect Faces
            display = frame.copy()
            faces, landmarks = face_detector.detect(Image.fromarray(frame))
            kids = 0
            x_face_origin = 0
            y_face_origin = 0
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

                        x_face_origin += int(gaze_origin[0])
                        y_face_origin += int(gaze_origin[1])

                        attention += abs(int(100 * np.sin(gaze[1])))

                # roll, pitch = calc_roll_and_pitch(x_face_origin, y_face_origin, kids, frame.shape)
                pitch, roll = calc_roll_and_pitch(x_face_origin, y_face_origin, kids, frame.shape)
                avg_roll += roll
                avg_pitch += pitch
            else:
                avg_roll += 50
                avg_pitch += 50
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

            if producer_frames == args.producer_frames:
                attention_avg, kids_avg = calc_avg_attention_and_kids(args, attention_avg, kids_avg)
                send_messages(kids_avg, attention_avg, roll=avg_roll/args.producer_frames, pitch=avg_pitch/args.producer_frames)
                producer_frames, attention_avg, kids_avg, avg_roll, avg_pitch = 0, 0, 0, 0, 0
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


def send_messages(kids_avg, attention_avg, roll=None, pitch=None):
    message_camera = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                      'n_kids': str(kids_avg), 'attention': str(attention_avg)}

    rabbitMQ.publish(exchange='main',
                     routing_key='camera',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_camera)

    message_servo = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'roll': roll, 'pitch': pitch}

    rabbitMQ.publish(exchange='main',
                     routing_key='cam.pose',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_servo)


def calc_avg_attention_and_kids(args, attention_avg, kids_avg):
    attention_avg /= args.producer_frames
    attention_avg = 100 - attention_avg
    kids_avg /= args.producer_frames
    return attention_avg, kids_avg


def calc_roll_and_pitch(x_face_origin, y_face_origin, kids, frame_shape):
    if kids > 0:
        x_face_origin /= kids
        y_face_origin /= kids
        roll = x_face_origin*100 / frame_shape[1]
        pitch = y_face_origin*100 / frame_shape[0]
        pitch = 100 - pitch
        roll = 100 - roll
    else:
        roll, pitch = 50, 50
    return roll, pitch


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--weights', '-w', type=str, default='/home/matanweks/Apps/RoboFriend/models/weights/gazenet.pth')
    parser.add_argument('--camera', '-cam', type=int, default=0,
                        help='Choose which camera is working (in my computer 2 - built-in camera and 0 USB cam')

    parser.add_argument('--producer_frames', '-produce', type=int, default=5,
                        help='Choose which camera is working (in my computer 2 - built-in camera and 0 USB cam')

    args = parser.parse_args()

    gaze_detection(args=args)
