import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime
import time
import utils
import subprocess

enable_print = False

if enable_print: print('Running Video Service')
story = utils.PlayMovie()
# stopwatch = sched.scheduler(time.time, time.sleep)

timer_process = False

def trigger_stopwatch(duration, page):
    if enable_print: print('----- Starting Stopwatch -----')
    stopwatch = subprocess.Popen(['python3', 'services/StopWatch.py', '--duration', str(duration), '--page', str(page)], shell=False)
    return stopwatch

def callback(ch, method, properties, body):
    global timer_process
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    # global page
    message = json.loads(body)
    if enable_print: print(" Video Callback -> [x] %r" % message)

    if message['action'] == 'play':
        page = message["page"]
        if enable_print: print(f'Playing movie {message["story"]}, page {message["page"]}, from {message["from_to"][0]} to {message["from_to"][1]}')

        page = message["page"]
        start_position = message["from_to"][0]
        stop_position = message["from_to"][1]

        story.play_page(start_position=start_position, stop_position=stop_position)
        duration = int(abs(stop_position - start_position))
        if enable_print: print('duration:', duration)
        timer_process = trigger_stopwatch(duration, page)

    elif message['action'] == 'pause':
        try:
            timer_process.kill()
            if enable_print: print('killed the timer!')
        except:
            if enable_print: print('No stopwatch process alive')

        story.pause()

    elif message['action'] == 'stop':
        try:
            timer_process.kill()
        except:
            if enable_print: print('No stopwatch process alive')

        story.stop()

    elif message['action'] == 'start':
        story.choose_story(path='Videos/' + message["story"] + '.mp4')

    else:
        if enable_print: print('Non-recognized command')


def callback_stopwatch(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)
    if message['command'] == 'stopwatch_alarm' and message['state'] == 'done':
        send_EoP(message['page'])


def send_EoP(page):
    ''' Send a message to StoryTeller to indicate page ended (End of Page)'''
    story.pause()
    message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                'state': 'EoP',
                'page_ended': page
                }

    rabbitMQ.publish(exchange='main', routing_key='video.state', body=message)
    if enable_print: print(" --> [x] Sent %r:%r" % ('video.state', message))


rabbitMQ = RbmqHandler('video_service')
rabbitMQ.declare_exchanges(['main'])

# Setup to listen to messages with key "video.action" - currently only service publishing on this is StoryTeller
rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'video.action', 'callback': callback})
rabbitMQ.queues.append({'name': 'stopwatch', 'exchange': 'main', 'key': 'stopwatch', 'callback': callback_stopwatch})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()


