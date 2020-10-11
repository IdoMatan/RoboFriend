import os
import sys
import cv2
import torch
import argparse
import traceback
import numpy as np
from PIL import Image
from mtcnn import FaceDetector
import matplotlib.pyplot as plt
from datetime import datetime
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
import utils
from models import gazenet
import time

# from Arduino_control.ArduinoServoControl import *  # TODO uncomment

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
    print('Running Camera Service')

    gaze_model, face_detector = load_trained_models()

    fps, frame_num, frame_samples, roll, pitch, avg_roll, avg_pitch, max_angle, producer_frames, \
    attention_avg, kids_avg, x_face_origin, y_face_origin, frame_faces, frames_faces_locations, fps_timer, \
    duration_timer, cap, state_collection_duration, collection_mode, collection_frames \
        = init_state(args)

    while True:
        plt.close()
        try:
            ret, frame = cap.read()
            frame = frame_arrangements(frame)
            img_h, img_w, _ = np.shape(frame)
            frame_num += 1

            display = update_plot(display=None, frame=frame, mode='copy')

            faces, landmarks = face_detector.detect(Image.fromarray(frame)) # Detect Faces
            kids, x_face_origin, y_face_origin, attention = reset_params()

            if len(faces) != 0:
                for f, lm in zip(faces, landmarks):
                    # Confidence check
                    if(f[-1] > 0.98):
                        # Crop and normalize face Face
                        face, gaze_origin, M = utils.normalize_face(lm, frame)
                        kids += 1

                        with torch.no_grad():
                            gaze = gaze_model.get_gaze(face)  # Predict gaze
                            gaze = gaze[0].data.cpu()

                        # Draw results
                        display = update_plot(display=display, gaze_origin=gaze_origin, gaze=gaze, mode='draw gaze')

                        x_face_origin += int(gaze_origin[0])
                        y_face_origin += int(gaze_origin[1])
                        attention += abs(int(100 * np.sin(gaze[1])))
                        if collection_mode:
                            frame_faces.append(gaze_origin)

                # roll, pitch = calc_roll_and_pitch(x_face_origin, y_face_origin, kids, frame.shape)
                pitch, roll = calc_roll_and_pitch(x_face_origin, y_face_origin, kids, frame.shape)
                avg_roll += roll
                avg_pitch += pitch
            else:
                avg_roll += 50
                avg_pitch += 50

            # Calc FPS
            if (frame_num == frame_samples):
                fps, fps_timer, frame_num = calc_fps(fps_timer, frame_samples)
                display = update_plot(display=display, fps=fps, mode='put text')

            # plot
            update_plot(display=display, mode='plot')

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                cap.release()
                break
            if collection_mode:
                if len(frame_faces):
                    frames_faces_locations.append(frame_faces)
                frame_faces = []
            # state collection
            if time.time() - duration_timer >= state_collection_duration[collection_mode]:
                # print(collection_mode, ' duration: ', time.time() - duration_timer)
                if not collection_mode:
                    toggle_servos(False)
                    collection_mode = 1
                    duration_timer = time.time()
                else:
                    toggle_servos(True)
                    attention_avg, kids_avg = calc_avg_attention_and_kids(collection_frames, attention_avg, kids_avg)
                    send_state(kids_avg, attention_avg, frames_faces_locations)
                    producer_frames, attention_avg, kids_avg = 0, 0, 0
                    frame_faces, frames_faces_locations = [], []
                    collection_mode = 0
                    collection_frames = 0
                    duration_timer = time.time()


            else:
                if kids > 0:
                    attention /= kids
                attention_avg += attention
                kids_avg += kids
                collection_frames += 1

            # Producer for roll-pitch
            if producer_frames == args.producer_frames:
                send_massage_roll(roll=avg_roll/args.producer_frames, pitch=avg_roll/args.producer_frames)
                producer_frames, avg_roll, avg_pitch = 0, 0, 0
            else:
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


def send_state(kids_avg, attention_avg, frames_faces_locations):
    message_camera = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                      'n_kids': kids_avg, 'attention': attention_avg,
                      'excitation': calc_excitation(frames_faces_locations)}

    rabbitMQ.publish(exchange='main',
                     routing_key='camera',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_camera)


def send_massage_roll(roll, pitch):
    message_servo = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'roll': roll, 'pitch': pitch}

    rabbitMQ.publish(exchange='main',
                     routing_key='servos.pose',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_servo)


def toggle_servos(enable):
    message_servo = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'command': 'toggle', 'enable': enable}

    rabbitMQ.publish(exchange='main',
                     routing_key='servos.toggle',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_servo)


# def calc_excitation(frames_faces_locations):
#     excitation = 0
#     # print('N frames: ', len(frames_faces_locations))
#     if len(frames_faces_locations):
#         for i in range(1, len(frames_faces_locations)):
#             for j in range(len(frames_faces_locations[i])):
#                 excitation += min(np.linalg.norm(np.array(frames_faces_locations[i-1])-np.array(frames_faces_locations[i][j]), axis=1))
#             excitation /= j+1
#         excitation /= i+1
#     # print(f'Excitation: {excitation}')
#     return excitation


def calc_excitation(frames_faces_locations):
    excitation = 0
    # print('N frames: ', len(frames_faces_locations))
    if len(frames_faces_locations):
        for i in range(1, len(frames_faces_locations)):
            temp_excitation = np.zeros(len(frames_faces_locations[i]))
            for j in range(len(frames_faces_locations[i])):
                temp_excitation[j] = min(np.linalg.norm(np.array(frames_faces_locations[i-1])-np.array(frames_faces_locations[i][j]), axis=1))

            if len(frames_faces_locations[i]) > len(frames_faces_locations[i - 1]):
                n = len(frames_faces_locations[i]) - len(frames_faces_locations[i-1])
                excitation += np.sum(n_smallest(temp_excitation, n))
                excitation /= n
            else:
                excitation += np.sum(temp_excitation)
                excitation /= j+1
        excitation /= i+1
    print(f'Excitation: {excitation}')
    return excitation


def n_smallest(a, n):
    return np.partition(a, n)[:n]


def calc_avg_attention_and_kids(frames, attention_avg, kids_avg):
    attention_avg /= frames
    attention_avg = 100 - attention_avg
    kids_avg /= frames
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


def calc_fps(fps_timer, frame_samples):
    fps = time.time() - fps_timer
    fps = frame_samples / fps
    fps_timer = time.time()
    frame_num = 0
    return fps, fps_timer, frame_num


def update_plot(display=None, mode=None, frame=None, gaze_origin=None, gaze=None, fps=None):
    if mode == 'copy':
        display = frame.copy()
    if mode == 'draw gaze':
        display = cv2.circle(display, gaze_origin, 3, (0, 255, 0), -1)
        display = utils.draw_gaze(display, gaze_origin, gaze, color=(255, 0, 0), thickness=2)
    if mode == 'put text':
        display = cv2.putText(display, 'FPS: {:.2f}'.format(fps), (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 1,
                              cv2.LINE_AA)
    if mode == 'plot':
        cv2.imshow('Gaze Demo', cv2.cvtColor(display, cv2.COLOR_RGB2BGR))
    return display


def load_trained_models():
    device = torch.device("cuda:0" if (torch.cuda.is_available() and not args.cpu) else "cpu")
    model = gazenet.GazeNet(device)

    if(not torch.cuda.is_available() and not args.cpu):
        print('Tried to load GPU but found none. Please check your environment')

    state_dict = torch.load(args.weights, map_location=device)
    model.load_state_dict(state_dict)
    print('Model loaded using {} as device'.format(device))

    model.eval()
    face_detector = FaceDetector(device=device)

    return model, face_detector


def init_state(args):
    state_collection_duration = [3, 2]

    fps = 0
    frame_num = 0
    frame_samples = 6
    roll, pitch = 50, 50
    avg_roll, avg_pitch = 0, 0
    max_angle = 180
    producer_frames = 0
    attention_avg, kids_avg = 0, 0
    x_face_origin, y_face_origin = 0, 0
    frame_faces, frames_faces_locations = [], []

    collection_mode = 0
    collection_frames = 0
    fps_timer = time.time()
    duration_timer = time.time()
    cap = cv2.VideoCapture(args.camera)

    return fps, frame_num, frame_samples, roll, pitch, avg_roll, avg_pitch, max_angle, producer_frames, \
           attention_avg, kids_avg, x_face_origin, y_face_origin, frame_faces, frames_faces_locations, fps_timer, \
           duration_timer, cap, state_collection_duration, collection_mode, collection_frames


def frame_arrangements(frame):
    frame = frame[:, :, ::-1]
    # # frame = cv2.flip(frame, 1)
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame


def reset_params():
    kids = 0
    x_face_origin = 0
    y_face_origin = 0
    attention = 0
    return kids, x_face_origin, y_face_origin, attention


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--weights', '-w', type=str, default='/home/matanweks/Apps/RoboFriend/models/weights/gazenet.pth')
    parser.add_argument('--camera', '-cam', type=int, default=0,  # 2,
                        help='Choose which camera is working (in my computer 2 - built-in camera and 0 USB cam')

    parser.add_argument('--producer_frames', '-produce', type=int, default=5,
                        help='producer frames')

    args = parser.parse_args()

    gaze_detection(args=args)
