from kafka import KafkaConsumer, KafkaProducer
import json
import subprocess
import time
import atexit

# ------------------------------------------------ Init subprocess --------------------------------------------------

process_list = []


def terminate_subprocesses(running_processes):
    print('Closing Subprocesses....')
    for process in running_processes:
        if process == zookeeper:
            subprocess.call('./bin/zookeeper-server-stop.sh')
        elif process == kafka:
            subprocess.call('./bin/kafka-server-stop.sh')
        else:
            process.terminate()

        time.sleep(1)


atexit.register(terminate_subprocesses, process_list)


print('----- Starting Kafka and ZooKeeper..... -----')
kafka = subprocess.Popen('bin/kafka-server-start.sh config/server.properties', shell=True)
process_list.append(kafka)

zookeeper = subprocess.Popen('bin/zookeeper-server-start.sh config/zookeeper.properties', shell=True)
process_list.append(zookeeper)

time.sleep(10)

# create topics
print('----- Creating topics if needed..... -----')

subprocess.call('./init_kafka_topics.sh')

print('----- Starting MicService -----')
mic_process = subprocess.Popen('python MicService.py', shell=True)
process_list.append(mic_process)

print('----- Starting CamService -----')
cam_process = subprocess.Popen('python CamService.py', shell=True)
process_list.append(cam_process)

print('----- Starting VideoService -----')
video_process = subprocess.Popen('python VideoService.py', shell=True)
process_list.append(video_process)

# print('----- Starting LoggingService -----')
# logging_service = subprocess.Popen('python LogService.py', shell=True)


producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

consumer.subscribe(['video', 'servos', 'algorithm'])


def execute_action(action, channel):
    pass


# ------------------------------------------------ Run Session --------------------------------------------------
pages = [0, 82, 159, 229, 310, 380, 466]
story = 'ApartmentForRent'
session = 1


for page, time_stamp in enumerate(pages):
    # run video
    print(f'Playing page', page, '/', len(pages))
    producer.send('video', value={'page': str(time_stamp), 'story': story}, key='VideoService')
    for message in consumer:
        if message.topic == 'video' and False:  # message.value['status'] == 'EoP':
            print('Page ended, waiting for action')
            producer.send('algorithm', value={'command': 'GetAction', 'session': str(session)}, key='MainService')
            producer.send('logger', value={'command': 'log_experience', 'session': str(session)}, key='MainService')

            # Wait for response from algo channel

        if message.topic == 'algorithm' and message.value['action'] is not None:
            execute_action(message.value['action'], channel='servos')
            break

