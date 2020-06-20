import pika

credentials = pika.PlainCredentials('rabbitmq', 'rabbitmq')

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='13.58.106.247', credentials=credentials))
channel = connection.channel()

channel.exchange_declare(exchange='actions', exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='actions', queue=queue_name, routing_key='motor.*')

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] %r" % body)


channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

channel.start_consuming()