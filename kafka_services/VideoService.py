import numpy as np
from kafka import KafkaProducer, KafkaConsumer
import json
import time
from VLC_app import *
import sys
import utils
import threading

def from_page_to_position(page=0):
    pages = [0, 10, 82100, 162000, 233000, 314000, 382000, 470000]
    return pages[page]


producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)


print('Running Video Service')
story = 'Apartment for Rent'

consumer.subscribe(['video'])
action = utils.PlayMovie()

position = None
page = None
previous_page = 0

for message in consumer:
    if message.topic == 'video' and message.key == 'MainService':
        page = int(message.value['page'])
        position = from_page_to_position(page=page)
        stop_position = from_page_to_position(page=page + 1)

        status = str(message.value['status'])
        if status == 'pause':
            action.pause()
        elif status == 'stop':
            action.stop()
        elif status == 'play':
            if position is not None:
                action.play(position=position)

    if page is not None:
        current_position = action.get_time()
        if current_position >= stop_position:
            # action.pause()
            producer.send('video', value={'page': str(page), 'story': story, 'status': 'done'}, key='VideoService')

        if previous_page != page:
            producer.send('video', value={'page': str(page), 'story': story, 'status': 'playing'}, key='VideoService')
            previous_page = page

