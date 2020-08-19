import numpy as np
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json

from Arduino_control.ArduinoServoControl import *


consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

consumer.subscribe(['servos'])
servo = ServoControl()


for message in consumer:
        if message.topic == 'servos' and message.key == 'MainService':
            try:
                roll = float(message.value['roll_servo'])
            except KafkaError:
                roll = 50

            pitch = float(message.value['pitch_servo'])
            left = float(message.value['left_servo'])
            right = float(message.value['right_servo'])

            servo.set_servo_angle(roll=50, pitch=50, left=25, right=25)
