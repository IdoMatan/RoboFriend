from sql_logging import *
from kafka import KafkaConsumer, KafkaProducer
import json
import subprocess

database = DatabaseLogger(user="postgres", password=None, host="13.58.106.247", port="5432", database="robo_friend")

database.connect()


consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)


consumer.subscribe(['camera', 'microphone', 'video', 'logging'])
time.sleep(1)


def calc_state():
    avg_attention, avg_noise, n_kids = database.get_state()


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

    elif message.topic == 'logging' and message.value['command'] == 'log_experience':
        # state: {average attention over page, average noise, n_kids
        database.log_experience(message.value['experience'])
