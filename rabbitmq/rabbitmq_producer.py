from rabbitMQ_utils import *
import time
import json
from datetime import datetime

rabbitMQ = RbmqHandler('producer_test')
rabbitMQ.declare_exchanges(['main'])

messageA = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'command': 'get manual action',
            'page': 3}


rabbitMQ.channel.basic_publish(exchange='main', routing_key='action.manual', body=json.dumps(messageA))

print(" [x] Sent %r:%r" % ('app', messageA))


# for i in range(4):
#
#     rabbitMQ.channel.basic_publish(exchange='main', routing_key='app', body=json.dumps(messageA))
#     print(" [x] Sent %r:%r" % ('app', messageA))
#
#     time.sleep(2)
#
#     rabbitMQ.channel.basic_publish(exchange='main', routing_key='servo', body=json.dumps(messageB))
#     print(" [x] Sent %r:%r" % ('Servo', messageB))
#
#     time.sleep(2)
#
# # rabbitMQ.close()

