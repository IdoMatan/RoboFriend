from kafka import KafkaProducer, KafkaConsumer
import json


producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                         value_deserializer=json.loads,
                         key_deserializer=bytes.decode)

consumer.subscribe(['algorithm'])

for message in consumer:

    if message.topic == 'algorithm' and message.key == '??' and message.value['status'] == '??':

        producer.send('algorithm', value={'command': 'GetAction', 'session': str(session)}, key='MainService')
        producer.send('logger', value={'command': 'log_experience', 'session': str(session)}, key='MainService')
