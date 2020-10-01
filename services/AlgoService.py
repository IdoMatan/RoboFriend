import time
import sys, os
from ActorCriticAlgo import *
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime

'''
Robo-Friend project - Algorithm Service
-----------------------------------------
The 'Brain' part of the code.
Listen to state metrics from mic, cam and storyteller services and log experiences
On demand, calculate action based on accumulated state

Listening to following channels for metrics:
    - MicService - volume and deviation metrics
    - CamService - N_kids, attention, excitation
    - StoryTeller - page_num
    
Listen to StoryTeller service for 'GetAction' command

General working scheme is as follows:

*** September 2020 ***
*** Matan Weksler & Ido Glanz ***

'''
enable_print = True

current_page = 0

STATE_VECTOR_LEN = 7
ACTION_SPACE = 4


def callback_metric(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print("AlgoService: Metrics Callback -> [x] %r" % message)

    if method.routing_key == 'microphone':
        # -> microphone messages are cached until a camera message with remaining params arrive
        env.mic_buffer.append(volume=message.get('volume'), noise_diff=message.get('sound_diff'))

    if method.routing_key == 'camera':
        # a -> state vector is constructed and logged
        env.state_buffer.add_state(page=current_page,
                                   n_kids=message.get('n_kids'),
                                   attention=message['attention'],
                                   excitation=message['excitation'],
                                   volume=env.mic_buffer.get_avg('volume'),
                                   sound_diff=env.mic_buffer.get_avg('noise_diff'),
                                   prev_action='auto')
        env.mic_buffer.reset()


def callback_action(ch, method, properties, body):
    global current_page, trainer, a2c, optimizer
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print("AlgoService: StoryTeller Callback -> [x] %r" % message)

    if method.routing_key == 'video.action':
        if message['action'] == 'start':
            # update env & episode and init trainer module
            env.update(message['story'], stories[message['story']], session=message['session'])
            episode.story_name = message['story']
            episode.uuid = message['session']

            trainer = Trainer(env.action_space.n, STATE_VECTOR_LEN)
            a2c, optimizer = trainer.load_a2c(load=False)  # TODO - Add auto loading of model

            env.reset()   # reset both state and mic buffers

        if message['action'] == 'play':
            current_page = message['page']

    elif method.routing_key == 'action.get' and trainer is not None:
        # THIS IS BASICALLY THE "STEP" section of the algorithm
        current_state, reward, _ = env.step()

        if message['command'] == 'end_of_story':
            is_done = 1
            if enable_print: print('AlgoService -> story ended, running training cycle')
            trainer.train(episode, current_state)
            trainer.save_model()

        elif message['command'] == 'get_action':
            is_done = 0
            value, policy_dist = a2c.forward(current_state)   # each a vector of size n_actions (i.e. 10 for now)

            value = value.detach().numpy()[0, 0]
            distribution = policy_dist.detach().numpy()

            action = np.random.choice(ACTION_SPACE, p=np.squeeze(distribution))  # weighted choosing based on output
            log_prob = torch.log(policy_dist.squeeze(0)[action])
            entropy = -np.sum(np.mean(distribution) * np.log(distribution))
            episode.entropy += entropy

            episode.add_experience(Experience(episode.uuid, current_state, action, reward, None, value, log_prob))

            env.reset()

            action_string = env.action_space.action(action)

            # send back action if not in manual mode
            if not message['manual']:
                message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': action_string, 'story': None}
                rabbitMQ.publish(exchange='main', routing_key='action.execute', body=message)
                if enable_print: print(f'AlgoService -> Sent back to storyteller action: {action_string}, [{action}]')


# TODO - OPEN ISSUES:
'''
# Rewarding mechanism
# LTL constraints integration
# state vector normalizing
# in-page learning***

'''

# state_buffer = StateBuffer()
# mic_buffer = MicBuffer()
#TODO init actor critic modules etc.


with open('../StoryConfig.json') as json_file:
    stories = json.load(json_file)

# init empty env and episode objects (will be updated after 'start' message)
logger = setup_logger('logger', 'algo_log', f'episode_log_{time.strftime("%a,%d_%b_%Y_%H_%M_%S")}.json')

env = Environment()
episode = Episode(None, logger)
trainer, a2c, optimizer = None, None, None

# trainer = Trainer(ACTION_SPACE, STATE_VECTOR_LEN)
# a2c, optimizer = trainer.load_a2c(load=False)  # TODO - Add auto loading of model

rabbitMQ = RbmqHandler('algo_service')
rabbitMQ.declare_exchanges(['main'])

rabbitMQ.queues.append({'name': 'state_metrics', 'exchange': 'main', 'key': 'microphone', 'callback': callback_metric})
rabbitMQ.queues.append({'name': 'state_metrics', 'exchange': 'main', 'key': 'camera', 'callback': callback_metric})
rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'action.get', 'callback': callback_action})
rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'video.action', 'callback': callback_action})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()


