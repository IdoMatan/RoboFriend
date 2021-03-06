import json
import subprocess
import time

# ------------------------------------------------ Init subprocess --------------------------------------------------

# process_list = []


def terminate_subprocesses(running_processes):
    print('Closing Subprocesses gracefully....')
    for process in running_processes:
        if process['name'] == 'zookeeper':
            subprocess.call('bin/zookeeper-server-stop.sh')
            time.sleep(2)
        elif process['name'] == 'kafka':
            subprocess.call('bin/kafka-server-stop.sh')
            time.sleep(2)
        else:
            print(f'Closing process: {process["name"]}')
            process['app'].kill()
            _,_ = process['app'].communicate()
            time.sleep(1)


def services():
    p_list = []

    print('----- Starting StoryTeller Service -----')
    story_teller = subprocess.Popen(['python3', 'services/StoryTeller.py'], shell=False)
    p_list.append({'name': 'story_teller', 'app': story_teller})

    print('----- Starting MicService -----')
    mic_process = subprocess.Popen(['python3', 'services/MicService.py'], shell=False)
    p_list.append({'name': 'mic_process', 'app': mic_process})

    print('----- Starting CamService -----')
    cam_process = subprocess.Popen(['python3', 'services/CamService.py'], shell=False)
    p_list.append({'name': 'cam_process', 'app': cam_process})

    print('----- Starting VideoService -----')
    video_process = subprocess.Popen(['python3', 'services/VideoService.py'], shell=False)
    p_list.append({'name': 'video_process', 'app': video_process})

    print('----- Starting LoggingService -----')
    logging_service = subprocess.Popen('python3 services/LogService.py', shell=True)
    p_list.append({'name': 'logging_service', 'app': logging_service})

    print('----- Starting Servos -----')
    servo_service = subprocess.Popen(['python3', 'services/ServoService.py'], shell=False)
    p_list.append({'name': 'servo_service', 'app': servo_service})

    print('----- Starting StoryTeller Service -----')
    speaker_service = subprocess.Popen(['python3', 'services/SpeakerService.py'], shell=False)
    p_list.append({'name': 'speaker_service', 'app': speaker_service})

    print('----- Starting StoryTeller Service -----')
    algo_service = subprocess.Popen(['python3', 'services/AlgoService.py'], shell=False)
    p_list.append({'name': 'algo_service', 'app': algo_service})

    return p_list
