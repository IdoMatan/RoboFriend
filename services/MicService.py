import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import json
from rabbitmq.rabbitMQ_utils import *
import sounddevice as sd
import numpy as np
from datetime import datetime
import pika

'''
Robo-Friend project - Microphone Service
-------------------------------------------
Averages N seconds of noise and sends average volume and sound waviness (average derviative)

service name: 'mic_service'
Rbmq key: microphone
exchange: main

message arguments:
    volume [float] - average noise level
    sound_diff [float] - average derivative of sound vector

*** September 2020 ***
*** Matan Weksler & Ido Glanz ***

'''

fs = 44100  # Sample rate
seconds = 2  # Duration of recording

print('Running Microphone Service')

rabbitMQ = RbmqHandler('mic_service')
rabbitMQ.declare_exchanges(['main'])

while 1:
    record = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished

    volume = np.sqrt(np.sum(record**2))
    sound_diff = np.sqrt(np.sum(np.diff(np.sum(record, 1))**2))

    # print(f'volume= {volume}, sound_diff={sound_diff}')

    messageA = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'volume': float(volume),'sound_diff': float(sound_diff)}

    rabbitMQ.publish(exchange='main',
                     routing_key='microphone',
                     body=messageA)

