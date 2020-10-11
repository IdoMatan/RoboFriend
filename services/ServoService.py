import numpy as np
import json
import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
from Arduino_control.ArduinoServoControl import *
import threading


'''
Robo-Friend project - Servo control Service
-------------------------------------------
Control the servos thru the com port. Supports pre-set moves or feed of roll/pitch for tracking

service name: 'servo_service'
Rbmq key: servos
exchange: main

message arguments:
    command [string] - ['Move head', 'Wave hands','explorer', 'track_faces]
    enable [False/True] - main enable for servo movement
    roll, pitch, right, left [int] - servo angles (in deg) 

*** September 2020 ***
*** Matan Weksler & Ido Glanz ***

'''

enable_print = False

print('Running Servo Service')
testing = True

if not testing:
    servo = ServoControl()


# def callback(ch, method, properties, body):
#     if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
#         return
#     message = json.loads(body)
#
#     if message['command'] == 'Move head':
#         servo.set_servo_angle(roll=50, pitch=50)
#         time.sleep(1)
#         servo.set_servo_angle(roll=10, pitch=50)
#         time.sleep(1)
#         servo.set_servo_angle(roll=50, pitch=10)
#         time.sleep(1)
#         servo.set_servo_angle(roll=80, pitch=50)
#         time.sleep(1)
#         servo.set_servo_angle(roll=50, pitch=50)
#         time.sleep(1)
#
#     elif message['command'] == 'Wave hands':
#         servo.set_servo_angle(left=25, right=25)
#         time.sleep(1)
#         servo.set_servo_angle(left=10, right=10)
#         time.sleep(1)
#         servo.set_servo_angle(left=40, right=40)
#         time.sleep(1)
#         servo.set_servo_angle(left=25, right=25)
#         time.sleep(1)
#
#     elif message['command'] == 'explorer':
#         servo.set_servo_angle(roll=50, pitch=50, left=25, right=10)
#         time.sleep(3)
#         for i in range(7):
#             servo.set_servo_angle(roll=50, pitch=10)
#             time.sleep(10)
#             servo.set_servo_angle(roll=50, pitch=90)
#             time.sleep(4)
#             servo.set_servo_angle(roll=50, pitch=50)
#             time.sleep(10)
#
#     elif message['command'] == 'track_faces':
#         servo.set_servo_angle(roll=message["roll"],
#                               pitch=message["pitch"])
#
#     else:
#         if enable_print: print('Command not supported yet')
#         # servo.set_servo_angle(roll=message["roll"],
#         #                       pitch=message["pitch"],
#         #                       left=message["left"],
#         #                       right=message["right"])


# ------ Init RabbitMQ --------------------------------------------------------------------------------------------

PARAMS = {'command': None, 'enable': False, 'roll': 50, 'pitch': 50, 'right': 10, 'left': 10, 'counter': 0}


def rbmq_thread():
    global PARAMS
    rabbitMQ = RbmqHandler('servo_service')
    rabbitMQ.declare_exchanges(['main'])

    def callback(ch, method, properties, body):
        global PARAMS
        if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
            return
        message = json.loads(body)
        print(message)
        for key in PARAMS.keys():
            if message.get(key) is not None:
                PARAMS[key] = message.get(key)
            PARAMS['counter'] = PARAMS['counter'] + 1

    rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'servos.*', 'callback': callback})
    rabbitMQ.setup_queues()
    rabbitMQ.start_consume()


# ------ Main ------------------------------------------------------------------------------------------------

rbmq = threading.Thread(target=rbmq_thread)
rbmq.start()

head_movement = [(50, 50), (10, 50), (50, 10), (80, 50), (50, 50)]
wave_hand = [(25, 25), (10, 10), (40, 40), (25, 25)]
explorer = [(50, 10), (50, 90), (50, 50)]

presets = {'Move head': head_movement, 'Wave hands': wave_hand, 'explorer': explorer}


def get_params():
    return PARAMS


def main():
    start_time = time.time()
    pose_pointer = 0
    last_command = None
    last_message_num = PARAMS['counter']

    while True:
        params = get_params()

        if params.get('command') in presets.keys() and (params.get('command') != last_command or params['counter'] != last_message_num):
            last_message_num = params['counter']
            if params.get('command') != last_command:
                pose_pointer = 0
                last_command = params.get('command')

        if params.get('enable') and abs(start_time - time.time()) > 1 and last_command is not None:
            start_time = time.time()
            if pose_pointer < len(presets.get(last_command)):
                action = presets.get(last_command)[pose_pointer]
                pose_pointer += 1
                if testing:
                    print(f'Setting servos to ({action[0]},{action[1]})')
                else:
                    servo.set_servo_angle(left=action[0], right=action[1])
                    pass

        elif params['command'] == 'track_faces':
            # in track faces mode the servos get values directly from cam service but conditioned on storyteller
            # or other service setting their params['command'= to 'track_faces'.
            if params['enable']:
                if testing:
                    print(f"Setting servos to ({params['roll']},{params['pitch']})")
                else:
                    servo.set_servo_angle(roll=params['roll'],
                                          pitch=params['pitch'],
                                          left=params['left'],
                                          right=params['right'])

        else:
            if enable_print: print('Command not supported yet/no enable sent')

        time.sleep(0.1)


main()
