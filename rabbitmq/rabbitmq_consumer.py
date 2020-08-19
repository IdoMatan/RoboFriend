from rabbitMQ_utils import *
import json


def callback_app(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    print(" App Callback -> [x] %r" % json.loads(body))


def callback_servo(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    print(" App Callback -> [x] %r" % json.loads(body))


rabbitMQ = RbmqHandler('consumer_test')
rabbitMQ.declare_exchanges(['main'])

rabbitMQ.queues.append({'name': 'app', 'exchange': 'main', 'key': 'app', 'callback': callback_app})
rabbitMQ.queues.append({'name': 'servo', 'exchange': 'main', 'key': 'action.manual', 'callback': callback_servo})

rabbitMQ.setup_queues()

rabbitMQ.start_consume()

# channel.basic_publish(
#     exchange='main', routing_key=routing_key, body=message)
# print(" [x] Sent %r:%r" % (routing_key, message))
#
#
# connection.close()