import sys, os, time
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import json
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime

enable_print = False

class StoryTeller:
    def __init__(self):
        self.story_name = None
        self.pages = None
        self.actions = None
        self.session = None
        self.manual = None
        self.current_page = None
        self.cam_mode = None

    def update(self, story_name, story_config, session, mode):
        self.story_name = story_name
        self.pages = story_config['pages']
        self.actions = story_config['actions']
        self.session = session
        self.manual = mode
        self.current_page = 0

    def play_pause(self, play):
        ''' play or pause video service '''
        if enable_print: print(f'Playing page', self.current_page, '/', len(self.pages))
        video_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                         'action': play,
                         'story': self.story_name,
                         'page': self.current_page,
                         'from_to': [self.pages[self.current_page], self.pages[self.current_page+1]]
                         }

        rabbitMQ.publish(exchange='main', routing_key='video.action', body=video_message)
        if enable_print: print(" [x] Sent %r:%r" % ('video', video_message))

        if play == 'play':
            self.cam_mode = 'track_faces'
        # servo_message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        #                  'command': 'track_faces',
        #                  'manual': story.manual
        #                  }
        # rabbitMQ.publish(exchange='main', routing_key='servos', body=servo_message)
        # print(" [x] Sent %r:%r" % ('servo', servo_message))

    # def pause(self):


def callback_app(ch, method, properties, body):
    ''' Called everything a message from app arrives '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print(" --> App Callback -> [x] %r" % message)
    if message['action'] == 'initial_start':
        story.update(message['story_name'], message['story'], message['session'], mode=message['manual'])
        story.play_pause('start')
        time.sleep(2)  #TODO - see if can be reduced
        story.play_pause('play')
    elif message['action'] == 'play':
        story.play_pause('play')
    elif message['action'] == 'pause':
        story.play_pause('pause')
    else:
        if enable_print: print('non-supported action')


def callback_eop(ch, method, properties, body):
    ''' Called when video sends End of Page message '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if message['state'] == 'EoP':
        if message['page_ended'] >= len(story.pages):
            if enable_print: print('Story Ended')
            pass

        else:
            story.current_page += 1
            packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                       'command': 'get action',
                       'page': message['page_ended'],
                       'manual': story.manual
                       }
            rabbitMQ.publish(exchange='main', routing_key='action.get', body=packet)
            if enable_print: print(" [x] Sent %r:%r" % ('video', message))

    if enable_print: print(" --> EoP Callback -> [x] %r" % message)


def callback_action(ch, method, properties, body):
    ''' Called when video sends End of Page message
    Supported actions: ["Play next page", "Wave hands", "Move head", "Ask question"]
    '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print(" --> EoP Callback -> [x] %r" % message)

    if message['action'] == 'Play next page':
        if enable_print: print('Continuing to next page')
        story.play_pause('play')

    elif message['action'] == 'Wave hands' or message['action'] == 'Move head':
        if enable_print: print(message['action'])
        story.cam_mode = 'preset_action'
        packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                  'command': message['action'],
                  'manual': story.manual
                  }
        rabbitMQ.publish(exchange='main', routing_key='servos', body=packet)
        if enable_print: print(" [x] Sent %r:%r" % ('servo', message))
        time.sleep(5)
        if enable_print: print('Finished action, moving on to next page....')
        story.play_pause('play')

    elif message['action'] == 'Ask question':
        if enable_print: print('Ask a question - not implemented yet, continuing to next page')
        story.play_pause('play')


def callback_cam(ch, method, properties, body):
    '''
    Transfer pose angles to serovs (depending on mode)
    '''
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if story.cam_mode == 'track_faces':
        packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                  'command': story.cam_mode,
                  'roll': message['roll'],
                  'pitch': message['pitch']}

        rabbitMQ.publish(exchange='main', routing_key='servos', body=packet)
        if enable_print: print(" [x] Sent %r:%r" % ('servo', message))

    if enable_print: print(" --> Camera pose Callback -> [x] %r" % message)

story = StoryTeller()   # create blank instance of storyteller

# ------ RabbitMQ setup ------------------------------------------------------------------------------------------

rabbitMQ = RbmqHandler('StoryTeller')
rabbitMQ.declare_exchanges(['main'])
rabbitMQ.queues.append({'name': 'app', 'exchange': 'main', 'key': 'app', 'callback': callback_app})
rabbitMQ.queues.append({'name': 'video', 'exchange': 'main', 'key': 'video.state', 'callback': callback_eop})
rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'action.execute', 'callback': callback_action})
rabbitMQ.queues.append({'name': 'cam', 'exchange': 'main', 'key': 'cam.pose', 'callback': callback_cam})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()
