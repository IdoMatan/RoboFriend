from kafka import KafkaProducer
import time

producer = KafkaProducer(bootstrap_servers='localhost:9092')
producer.send('test_ido', b'Hello, World!')

producer.send('test_ido', key=b'message-two', value=b'This is Kafka-Python')
time.sleep(1)
