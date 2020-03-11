from sql_logging import *
from kafka import KafkaConsumer, KafkaProducer
import json
import subprocess

database = DatabaseLogger(user="postgres", password=None, host="13.58.106.247", port="5432", database="robo_friend")

database.connect()
print('----- Connected to database -----')

print('----- Starting MicService -----')
mic_process = subprocess.Popen('python MicService.py', shell=True)

print('----- Starting CamService -----')
cam_process = subprocess.Popen('python CamService.py', shell=True)

print('----- Starting VideoService -----')
video_process = subprocess.Popen('python VideoService.py', shell=True)

print('Waiting for messages....')

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

consumer.subscribe(['camera', 'microphone', 'video'])
page = 1
action_time = time.time()
producer.send('action', value={'page': str(page), 'status': 'play'}, key='actionService')

for message in consumer:
        if message.topic == 'microphone':
            # print("Logging to database:", message.value['volume'], ', from:', message.key)
            database.log(mic=float(message.value['volume']))
        elif message.topic == 'camera':
            # print("Logging to database:", message.value['attention'], ', from:', message.key)
            database.log(attention=float(message.value['attention']), n_kids=float(message.value['kids']))
        elif message.topic == 'video':
            # print("Logging to database:", message.value['page'], ', from:', message.key)
            database.log(page_num=int(message.value['page']), story=message.value['story'])

        if time.time() - action_time > 20:
            page = page + 1
            producer.send('action', value={'page': str(page), 'status': 'play'}, key='actionService')
            action_time = time.time()
