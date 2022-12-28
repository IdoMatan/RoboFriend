from rabbitMQ_utils import RbmqHandler
import time
import json
from datetime import datetime

rabbitMQ = RbmqHandler('producer_test')
rabbitMQ.declare_exchanges(['main'])

messageA = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'message': 'HELLO WORLD!',
            'page': 10}

rabbitMQ.publish(exchange='main', routing_key='action.manual', body=messageA)

print(" [x] Sent %r:%r" % ('app', messageA))
