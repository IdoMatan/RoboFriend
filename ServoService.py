import numpy as np
from kafka import KafkaProducer, KafkaConsumer
import json

from Arduino_control.ArduinoServoControl import *


consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

consumer.subscribe(['servo'])
servo = ServoControl()

for message in consumer:
        if message.topic == 'servo':
            x_angle = float(message.value['x_servo_angle'])
            y_angle = float(message.value['y_servo_angle'])

            servo.set_servo_angle(x_angle, y_angle)
