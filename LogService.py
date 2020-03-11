from sql_logging import *
from kafka import KafkaConsumer
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

consumer.subscribe(['camera', 'microphone', 'video', 'logging'])

for message in consumer:
        if message.topic == 'microphone':
            print("Logging to database:", message.value['volume'], ', from:', message.key)
            database.log(mic=float(message.value['volume']))
        elif message.topic == 'camera':
            print("Logging to database:", message.value['attention'], ', from:', message.key)
            database.log(attention=float(message.value['attention']), n_kids=float(message.value['kids']))
        elif message.topic == 'video':
            print("Logging to database:", message.value['page'], ', from:', message.key)
            database.log(page_num=int(message.value['page']), story=message.value['story'])


# def process_topic_one(msg):
#     ...
#
# def process_topic_two(msg):
#     ...
#
# c.subscribe(['topic-one', 'topic-two])
#
# while True:
#     msg = c.poll(1.0)
#
#     if msg is None:
#         continue
#     if msg.error():
#         print("Consumer error: {}".format(msg.error()))
#         continue
#
#     if msg.topic() == "topic-one":
#         process_topic_one(msg)
#     elif msg.topic() == "topic-two":
#         process_topic_two(msg)
#
# c.close()