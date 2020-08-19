import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import json
from rabbitmq.rabbitMQ_utils import *
import sounddevice as sd
import numpy as np
from datetime import datetime
import pika

'''
Noise meter service
Sums 2 seconds of noise and send on rabbitmq (key: microphone)
'''
fs = 44100  # Sample rate
seconds = 2  # Duration of recording

print('Running Microphone Service')

rabbitMQ = RbmqHandler('mic_service')
rabbitMQ.declare_exchanges(['main'])

# print(" [x] Sent %r:%r" % ('app', messageA))


while 1:
    record = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished

    volume = np.sqrt(np.sum(record**2))
    messageA = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'volume': int(volume)}

    rabbitMQ.publish(exchange='main',
                     routing_key='microphone',
                     body=messageA)

