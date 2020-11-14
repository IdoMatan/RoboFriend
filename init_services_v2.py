import json
import subprocess
import time
from rabbitmq.rabbitMQ_utils import *

# ------------------------------------------------ Init subprocess --------------------------------------------------


class InitServices:
    def __init__(self):
        self.p_list = []
        self.services()

    def terminate_subprocesses(self):
        print('Closing Subprocesses gracefully....')
        for process in self.p_list:
            if process['name'] == 'zookeeper':
                subprocess.call('bin/zookeeper-server-stop.sh')
                time.sleep(2)
            elif process['name'] == 'kafka':
                subprocess.call('bin/kafka-server-stop.sh')
                time.sleep(2)
            else:
                print(f'Closing process: {process["name"]}')
                process['app'].kill()
                _, _ = process['app'].communicate()
                time.sleep(1)

    def services(self):
        print('----- Starting StoryTeller Service -----')
        story_teller = subprocess.Popen(['python3', 'services/StoryTeller.py'], shell=False)
        self.p_list.append({'name': 'story_teller', 'app': story_teller})

        print('----- Starting MicService -----')
        mic_process = subprocess.Popen(['python3', 'services/MicService.py'], shell=False)
        self.p_list.append({'name': 'mic_process', 'app': mic_process})

        print('----- Starting CamService -----')
        cam_process = subprocess.Popen(['python3', 'services/CamService.py'], shell=False)
        self.p_list.append({'name': 'cam_process', 'app': cam_process})

        print('----- Starting VideoService -----')
        video_process = subprocess.Popen(['python3', 'services/VideoService.py'], shell=False)
        self.p_list.append({'name': 'video_process', 'app': video_process})

        print('----- Starting LoggingService -----')
        logging_service = subprocess.Popen('python3 services/LogService.py', shell=True)
        self.p_list.append({'name': 'logging_service', 'app': logging_service})

        print('----- Starting Servos -----')
        servo_service = subprocess.Popen(['python3', 'services/ServoService.py'], shell=False)
        self.p_list.append({'name': 'servo_service', 'app': servo_service})

        print('----- Starting StoryTeller Service -----')
        speaker_service = subprocess.Popen(['python3', 'services/SpeakerService.py'], shell=False)
        self.p_list.append({'name': 'speaker_service', 'app': speaker_service})

        print('----- Starting StoryTeller Service -----')
        algo_service = subprocess.Popen(['python3', 'services/AlgoService.py'], shell=False)
        self.p_list.append({'name': 'algo_service', 'app': algo_service})


p = InitServices()
rabbitMQ = RbmqHandler('StoryTeller')
rabbitMQ.declare_exchanges(['main'])


def callback(ch, method, properties, body):
    message = json.loads(body)
    if message['action'] == 'EOS':
        p.terminate_subprocesses()


rabbitMQ.queues.append({'name': 'actions', 'exchange': 'main', 'key': 'action', 'callback': callback})
rabbitMQ.setup_queues()
rabbitMQ.start_consume()
