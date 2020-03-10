import numpy as np
from kafka import KafkaProducer
import json
import time
from VLC_app import *
import sys

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


print('Running Video Service')


for i in range(10):

    story = 'Apartment for Rent'
    page = i + 1
    producer.send('video', value={'page': str(page), 'story': story}, key='VideoService')
    time.sleep(10)


app = QApplication(sys.argv)
player = Player()
player.show()
player.resize(640, 480)

player.OpenFile('Videos/video_part1.mp4')

page = 1

session_number = 1