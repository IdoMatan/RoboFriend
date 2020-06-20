import pika
import sys

credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='13.58.106.247', credentials=credentials))
channel = connection.channel()

channel.exchange_declare(exchange='actions', exchange_type='topic')


routing_key = sys.argv[1] if len(sys.argv) > 2 else 'anonymous.info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'


channel.basic_publish(
    exchange='actions', routing_key=routing_key, body=message)
print(" [x] Sent %r:%r" % (routing_key, message))


connection.close()