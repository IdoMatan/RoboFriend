from rabbitMQ_utils import RbmqHandler
import json

# ----- callback/handlers
def callback_app(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    print(" App Callback -> [x] %r" % json.loads(body))


def callback_servo(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    print(" App Callback -> [x] %r" % json.loads(body))


rabbitMQ = RbmqHandler('consumer_test')  # set up a rabbimq handler object with unique ID 'consumer_test'
rabbitMQ.declare_exchanges(['main'])  # Declare the exchange

# Signup to topics you want to consume from (when message arrives, callback is called)
# each topic is fed into a queue which the app consumes
rabbitMQ.queues.append({'name': 'app', # name of topics to signup to
                        'exchange': 'main', # specify exchange (main)
                        'key': 'app', # filter messages by specific message key
                        'callback': callback_app}) # callback to be called when message arrives

rabbitMQ.queues.append({'name': 'servo',
                        'exchange': 'main',
                        'key': 'action.*',
                        'callback': callback_servo})

rabbitMQ.setup_queues()  # setup the queue per the defined above
rabbitMQ.start_consume()  # start consuming "main RUN in a sense"
