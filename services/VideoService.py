# from VLC_app import *
# import utils
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import json
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime
import time

print('Running Video Service')

# action = utils.PlayMovie()


def callback(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    # global page
    message = json.loads(body)
    print(" Video Callback -> [x] %r" % message)
    if message['action'] == 'play':
        page = message["page"]
        print(f'Playing movie {message["story"]}, page {message["page"]}, from {message["from_to"][0]} to {message["from_to"][1]}')

        #TODO Add here command to video player....
        #TODO Set stopwatch to trigger send_EoP() when finished page

        time.sleep(10)   #ToDO - REMOVE, ONLY FOR NOW
        send_EoP(page)

    elif message['action'] == 'pause':
        # Add here command to pause
        pass

    else:
        print('Non-recognized command')


def send_EoP(page):
    ''' Send a message to StoryTeller to indicate page ended (End of Page)'''

    message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'state': 'EoP',
                'page_ended': page
                }

    rabbitMQ.publish(exchange='main', routing_key='video.state', body=message)
    print(" --> [x] Sent %r:%r" % ('video.state', message))


rabbitMQ = RbmqHandler('video_service')
rabbitMQ.declare_exchanges(['main'])

# Setup to listen to messages with key "video.action" - currently only service publishing on this is StoryTeller
rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'video.action', 'callback': callback})
rabbitMQ.setup_queues()
rabbitMQ.start_consume()
