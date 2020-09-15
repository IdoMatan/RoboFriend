import numpy as np
import json
import os, sys
from Arduino_control.ArduinoServoControl import *

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *


def calc_angles(dx, dy):
    return 0, 0


def callback(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)

    pitch, yaw = calc_angles()

    x_angle = float(message.value['x_servo_angle'])
    y_angle = float(message.value['y_servo_angle'])

    servo.set_servo_angle(x_angle, y_angle)


# ------ Init RabbitMQ --------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('servo_service')
rabbitMQ.declare_exchanges(['main'])

# Setup to listen to messages with key "video.action" - currently only service publishing on this is StoryTeller
rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'servo', 'callback': callback})
rabbitMQ.setup_queues()
rabbitMQ.start_consume()

'''
# TO SEND METRICS DO:
message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'n_kids': n_faces, 'attention': attention_metric}

rabbitMQ.publish(exchange='main',
                 routing_key='camera',    # routing key could also be: camera.servo if sending direct angles
                 body=message)
'''



