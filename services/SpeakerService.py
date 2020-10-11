import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
import vlc
from pathlib import Path

'''
Robo-Friend project - Speaker Service
-----------------------------------------
Listen on Action channel and play a question from given sound files
(also listens to initial_start to update storyname and play messages for current page)

*** October 2020 ***
*** Matan Weksler & Ido Glanz ***

'''
enable_print = True


class mp3_player:
    def __init__(self, file_format):
        self.file_format = file_format
        self.storyname = None
        self.page = 0
        self.player = None

    def update(self, storyname=None, page=None):
        ''' Update page name or number (after getting params from app'''
        if storyname:
            self.storyname = storyname
        if page is not None:
            self.page = str(page + 1).zfill(3)

    def play(self):
        filename = self.file_format.format(story=self.storyname, page=self.page)
        if enable_print: print(filename)
        self.player = vlc.MediaPlayer(filename)
        self.player.play()


def callback(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print(message)
    if properties.app_id in ['app_service', 'test_service'] and message['action'] == 'initial_start':
        player.update(storyname=message['story'])
    if properties.app_id in ['app_service', 'test_service'] and message['action'] == 'play':
        player.update(page=message['page'])

    if properties.app_id in ['algo_service', 'app_service', 'test_service']:
        if message.get('action') == 'Ask question':
            # Got action!
            player.play()


path = Path(sys.path[0]).parent
player = mp3_player(file_format=str(path) + '/Questions/{story}/120722_{page}.mp3')


rabbitMQ = RbmqHandler('speaker')
rabbitMQ.declare_exchanges(['main'])

rabbitMQ.queues.append({'name': 'speaker', 'exchange': 'main', 'key': 'video.action', 'callback': callback})
rabbitMQ.queues.append({'name': 'speaker', 'exchange': 'main', 'key': 'action.execute', 'callback': callback})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()
