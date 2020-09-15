from kafka import KafkaConsumer

print('Waiting for messages....')
consumer = KafkaConsumer('test_ido', bootstrap_servers=['localhost:9092'])


for message in consumer:
        print(message.value)


