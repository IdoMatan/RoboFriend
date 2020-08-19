import numpy as np
import json
import os, sys
from Arduino_control.ArduinoServoControl import *
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *

enable_print = False

print('Running Servo Service')
servo = ServoControl()


def callback(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)

    if message['command'] == 'Move head':
        servo.set_servo_angle(roll=50, pitch=50)
        time.sleep(3)
        servo.set_servo_angle(roll=10, pitch=50)
        time.sleep(3)
        servo.set_servo_angle(roll=50, pitch=50)
        time.sleep(3)
        servo.set_servo_angle(roll=90, pitch=50)
        time.sleep(3)

    elif message['command'] == 'Wave hands':
        servo.set_servo_angle(left=25, right=25)
        time.sleep(3)
        servo.set_servo_angle(left=10, right=10)
        time.sleep(3)
        servo.set_servo_angle(left=40, right=40)
        time.sleep(3)
        servo.set_servo_angle(left=25, right=25)
        time.sleep(3)
    elif message['command'] == 'track_faces':
        servo.set_servo_angle(roll=message["roll"],
                              pitch=message["pitch"])
    else:
        if enable_print: print('Command not supported yet')
        # servo.set_servo_angle(roll=message["roll"],
        #                       pitch=message["pitch"],
        #                       left=message["left"],
        #                       right=message["right"])
# ------ Init RabbitMQ --------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('servo_service')
rabbitMQ.declare_exchanges(['main'])

# Setup to listen to messages with key "video.action" - currently only service publishing on this is StoryTeller
rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'servos', 'callback': callback})
rabbitMQ.setup_queues()
rabbitMQ.start_consume()