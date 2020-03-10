from kafka import KafkaConsumer, KafkaProducer
import json
import subprocess
import time

print('----- Starting Kafka and ZooKeeper -----')
kafka = subprocess.Popen('bin/kafka-server-start.sh config/server.properties', shell=True)
zookeeper = subprocess.Popen('bin/zookeeper-server-start.sh config/zookeeper.properties', shell=True)

time.sleep(5)

print('----- Starting MicService -----')
mic_process = subprocess.Popen('python MicService.py', shell=True)

print('----- Starting CamService -----')
cam_process = subprocess.Popen('python CamService.py', shell=True)

print('----- Starting VideoService -----')
video_process = subprocess.Popen('python VideoService.py', shell=True)

print('----- Starting LoggingService -----')
logging_service = subprocess.Popen('python LogService.py', shell=True)


producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

consumer.subscribe(['camera', 'microphone', 'video', 'servos'])


