import numpy as np
from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


print('Running Camera Service')


for i in range(600):

    kids = np.random.randint(1, 10)
    # attention = np.random.randint(0, 100)
    attention = 50 + 50 * np.sin(float(time.time()))
    producer.send('camera', value={'attention': str(attention), 'kids': str(kids)}, key='CamService')
    time.sleep(2)

