import sounddevice as sd
import numpy as np
from kafka import KafkaProducer
import json

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         key_serializer=str.encode,
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

fs = 44100  # Sample rate
seconds = 2  # Duration of recording

print('Running Microphone Service')

for i in range(600):
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished

    volume = np.sqrt(np.sum(myrecording**2))
    # print(i, float(volume), kids)
    producer.send('microphone', value={'volume': str(volume)}, key='MicService')





