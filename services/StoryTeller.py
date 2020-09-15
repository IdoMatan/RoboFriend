import sys, os, time
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import json
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime


class StoryTeller:
    def __init__(self):
        self.story_name = None
        self.pages = None
        self.actions = None
        self.session = None
        self.manual = None
        self.current_page = None

    def update(self, story_name, story_config, session, mode):
        self.story_name = story_name
        self.pages = story_config['pages']
        self.actions = story_config['actions']
        self.session = session
        self.manual = mode
        self.current_page = 0

    def play_pause(self, play):
        ''' play or pause video service '''
        print(f'Playing page', self.current_page, '/', len(self.pages))
        video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                         'action': play,
                         'story': self.story_name,
                         'page': self.current_page,
                         'from_to': [self.pages[self.current_page], self.pages[self.current_page+1]]
                         }

        rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
        print(" [x] Sent %r:%r" % ('video', video_message))

        servo_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                         'command': 'track_faces',
                         'manual': story.manual
                         }
        rabbitMQ.publish(exchange='main', routing_key='servo', body=servo_message)
        print(" [x] Sent %r:%r" % ('servo', servo_message))

    # def pause(self):


def callback_app(ch, method, properties, body):
    ''' Called everything a message from app arrives '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    print(" --> App Callback -> [x] %r" % message)
    if message['action'] == 'initial_start':
        story.update(message['story_name'], message['story'], message['session'], mode=message['manual'])
        story.play_pause('play')
    if message['action'] == 'play':
        story.play_pause('play')


def callback_eop(ch, method, properties, body):
    ''' Called when video sends End of Page message '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if message['state'] == 'EoP':
        if message['page_ended'] >= len(story.pages):
            print('Story Ended')
            pass

        else:
            story.current_page += 1
            packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                       'command': 'get manual action',
                       'page': message['page_ended'],
                       'manual': story.manual
                       }
            rabbitMQ.publish(exchange='main', routing_key='action.get', body=packet)
            print(" [x] Sent %r:%r" % ('video', message))

    print(" --> EoP Callback -> [x] %r" % message)


def callback_action(ch, method, properties, body):
    ''' Called when video sends End of Page message
    Supported actions: ["Play next page", "Wave hands", "Move head", "Ask question"]
    '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    print(" --> EoP Callback -> [x] %r" % message)

    if message['action'] == 'Play next page':
        print('Continuing to next page')
        story.play_pause('play')

    elif message['action'] == 'Wave hands' or message['action'] == 'Move head':
        print(message['action'])
        packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                  'command': message['action'] ,
                  'manual': story.manual
                  }
        rabbitMQ.publish(exchange='main', routing_key='servo', body=packet)
        print(" [x] Sent %r:%r" % ('servo', message))
        time.sleep(5)
        print('Finished action, moving on to next page....')
        story.play_pause('play')

    elif message['action'] == 'Ask question':
        print('Ask a question - not implemented yet, continuing to next page')
        story.play_pause('play')


story = StoryTeller()   # create blank instance of storyteller

# ------ RabbitMQ setup ------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('StoryTeller')
rabbitMQ.declare_exchanges(['main'])
rabbitMQ.queues.append({'name': 'app', 'exchange': 'main', 'key': 'app', 'callback': callback_app})
rabbitMQ.queues.append({'name': 'video', 'exchange': 'main', 'key': 'video.state', 'callback': callback_eop})
rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'action.execute', 'callback': callback_action})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()
