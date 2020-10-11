import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
# import utils
from datetime import datetime
import time
import numpy as np

# ------ Init RabbitMQ --------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('test_service')
rabbitMQ.declare_exchanges(['main'])


# ------ Test ServpService  --------------------------------------------------------------------------------------------

# commands: 'Move head', 'Wave hands','explorer'

def test_servo_service():
    enable = True
    command = 'Move head'
    roll = 50
    pitch = 40

    servo_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'command': command,
                'enable': enable,
                'roll': roll,
                'pitch': pitch}

    rabbitMQ.publish(exchange='main',
                     routing_key='servos',
                     body=servo_message)

    time.sleep(2)

    enable = False
    command = 'Move head'
    roll = 50
    pitch = 40

    servo_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'command': command,
                'enable': enable,
                'roll': roll,
                'pitch': pitch}

    rabbitMQ.publish(exchange='main',
                     routing_key='servos',
                     body=servo_message)


# ------ Test AlgoService  --------------------------------------------------------------------------------------------


def test_algo_service(enable_print=True):
    # ------------ send start message --------------------------------------------------------------------------------:
    video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'action': 'start',
                     'session': 111,
                     'story': 'AptForRent',
                     'page': 0,
                     'n_actions': 4,
                     'from_to': [0, 20]
                     }

    rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
    if enable_print: print(" [x] Sent %r:%r" % ('video', video_message))
    time.sleep(2)

    # ------------ send play message --------------------------------------------------------------------------------:
    video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'action': 'play',
                     'session': 111,
                     'story': 'AptForRent',
                     'page': 0,
                     'n_actions': 4,
                     'from_to': [0, 20]
                     }

    rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
    if enable_print: print(" [x] Sent %r:%r" % ('video', video_message))

    # ------------ send camera message --------------------------------------------------------------------------------:
    for i in range(4):
        time.sleep(5)
        send_state(np.random.randint(1,4), np.random.randint(0,100),np.random.randint(0,200))

    # ------------ send get action message ---------------------------------------------------------------------------:
    time.sleep(1)

    packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
               'command': 'get_action',
               'page': 0,
               'manual': False
               }
    rabbitMQ.publish(exchange='main', routing_key='action.get', body=packet)
    if enable_print: print(" [x] Sent %r:%r" % ('video', packet))

    for i in range(4):
        time.sleep(5)
        send_state(np.random.randint(1,4), np.random.randint(0,100),np.random.randint(0,200))

    # ------------ send get action message ---------------------------------------------------------------------------:
    time.sleep(1)


    packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
              'command': 'end_of_story',
              'page': 1000,
              'manual': False
              }
    rabbitMQ.publish(exchange='main', routing_key='action.get', body=packet)
# ---------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


def send_state(kids_avg, attention_avg, frames_faces_locations):
    message_camera = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                      'n_kids': kids_avg, 'attention': attention_avg,
                      'excitation': frames_faces_locations}

    rabbitMQ.publish(exchange='main',
                     routing_key='camera',
                     # routing key could also be: camera.servo if sending direct angles
                     body=message_camera)

    print(" [x] Sent %r:%r" % ('camera', message_camera))


# ------ Test SpeakeroService  ----------------------------------------------------------------------------------------

def test_speaker_service():
    page = 0
    story = 'FoxStory'
    enable_print = True
    video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'action': 'initial_start',
                     'session': 1,
                     'story': story,
                     'page': page,
                     'n_actions': 4,
                     'from_to': [0,20]
                     }

    rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
    if enable_print: print(" [x] Sent %r:%r" % ('video', video_message))

    time.sleep(1)

    video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                     'action': 'play',
                     'session': 0,
                     'story': story,
                     'page': 6,
                     'n_actions': 4,
                     'from_to': [0,20]
                     }

    rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
    if enable_print: print(" [x] Sent %r:%r" % ('video', video_message))

    time.sleep(1)

    message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': 'Ask question', 'story': None}
    rabbitMQ.publish(exchange='main', routing_key='action.execute', body=message)

    time.sleep(3)


test_algo_service()
# test_speaker_service()
