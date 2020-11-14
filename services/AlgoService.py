import time
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from ActorCriticAlgo import *
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

State Vector shape (25/10/20):

index | description            | Type     | range
-------------------------------------------------------
0     | page number            | int      | 0 to <10
1     | N_kids                 | int      | 0 to <6
2     | Attention              | float    | 0 to 100
3     | Excitement             | float    | 0 to ?
4     | volume                 | float    | 0 to ?
5     | sound_diff             | float    | 0 to ?
6     | prev_action            | int      | 0 to 4
7-10  | prev_action as one-hot | bool vec | 0/1
11-14 | acc_action as one-hot  | int vec  | 0 to <10 
15    | action at (page-1)     | int      | 0-4
16    | action at (page-2)     | int      | 0-4
17    | action at (page-3)     | int      | 0-4

*** September 2020 ***
*** Matan Weksler & Ido Glanz ***

'''
enable_print = True

current_page = 0

ACTION_SPACE = 4
STATE_VECTOR_LEN = int(7 + ACTION_SPACE*2 + 3)


def log_to_db(message):
    ''' Send message to logger '''
    rabbitMQ.publish(exchange='main', routing_key='log.state', body=message)
    if enable_print: print(f'AlgoService -> Sent to logger: {message}')

# ------------------------------------------ Callbacks from RabbitMQ messages -----------------------------------------
# ---------------------------------------------------------------------------------------------------------------------


def callback_metric(ch, method, properties, body):
    ''' Called every-time a message from cam or mic arrives, buffers them together (@ cam message rate) in a state buffer
    later generating an accumulated state vector '''
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


        # send to logger:
        message = env.state_buffer.format_as_log_message(env.state_buffer.states[-1, :])
        rabbitMQ.publish(exchange='main', routing_key='log.metric', body=message)
        if enable_print: print(f'AlgoService -> Sent to logger: {message}')

        env.mic_buffer.reset()


def callback_action(ch, method, properties, body):
    '''
    Called when storyteller asks for an a next action (based on accumulated state). This runs also in manual mode
    but does not send its output back to the storyteller (as this mode means the action in manually fed from app
    ** This is also called upon an EndOfStory message triggering a learning cycle
    '''
    global current_page, trainer, a2c, optimizer
    if properties.app_id == rabbitMQ.id:  # skip messages sent from the same process
        return
    message = json.loads(body)
    if enable_print: print("AlgoService: StoryTeller get action Callback -> [x] %r" % message)

    if method.routing_key == 'video.action':
        if message['action'] == 'start':
            # update env & episode and init trainer module
            env.update(message['story'], stories[message['story']], session=message['session'])
            episode.story_name = message['story']
            episode.uuid = message['session']
            print('message: ', message)
            trainer = Trainer(env.action_space.n, STATE_VECTOR_LEN, manual=message['manual'])
            a2c, optimizer = trainer.load_a2c(load=False)  # TODO - Add auto loading of model (DONE?)

            # diff constraints init
            trainer.diff_constraints_module = DiffConstraints_loss()
            trainer.diff_constraints_module.add_constraint(diff_constraints_diversity)
            trainer.diff_constraints_module.add_constraint(diff_constraints_do_not_repeat)

            env.reset()   # reset both state and mic buffers

        if message['action'] == 'play':
            current_page = message['page']

    elif method.routing_key == 'action.get' and trainer is not None:
        # THIS IS BASICALLY THE "STEP" section of the algorithm
        current_state, _ = env.step()

        if message['command'] == 'end_of_story':
            is_done = 1
            if enable_print: print('AlgoService -> story ended, running training cycle')
            trainer.train(episode, current_state)
            trainer.save_model()

            # send message to app to close everything and go home
            message = {'time': datetime.now().strftime("%m/%d/%Y %H:%M:%S"), 'command': 'end_of_story', 'story': None}
            rabbitMQ.publish(exchange='main', routing_key='action.get', body=message)

        elif message['command'] == 'get_action':
            is_done = 0
            value, policy_dist = a2c.forward(current_state)   # each a vector of size n_actions (i.e. 10 for now)

            value = value.detach().numpy()[0, 0]
            distribution = policy_dist.detach().numpy()

            print('Current state: ', current_state)
            print('Distribution: ', distribution)

            action = np.random.choice(ACTION_SPACE, p=np.squeeze(distribution))  # weighted choosing based on output
            log_prob = torch.log(policy_dist.squeeze(0)[action])
            entropy = -np.sum(np.mean(distribution) * np.log(distribution))
            episode.entropy += entropy

            env.prev_action.append(int(action))   # append action to prev_actions before calculating reward
            reward = env.calc_reward()

            episode.diff_constraints.append(trainer.diff_constraints_module.loss(current_state, policy_dist))

            episode.add_experience(Experience(episode.uuid, current_state.tolist(), action, reward.detach().tolist(), None, value, log_prob.tolist(), policy_dist=policy_dist),
                                   log=not message['manual'])

            env.prev_action.append(int(action))
            env.reset()

            action_string = env.action_space.action(action)

            # send back action if not in manual mode
            if not message['manual']:
                message = {'time': datetime.now().strftime("%m/%d/%Y %H:%M:%S"), 'action': action_string, 'story': None}
                rabbitMQ.publish(exchange='main', routing_key='action.execute', body=message)
                if enable_print: print(f'AlgoService -> Sent back to storyteller action: {action_string}, [{action}]')

            ### Send log message to logger
            message = env.state_buffer.format_as_log_message(current_state)
            message.update({'action': action_string})   # append the action as a string

            rabbitMQ.publish(exchange='main', routing_key='log.state', body=message)
            if enable_print: print(f'AlgoService -> Sent to logger: {message}')


    elif method.routing_key == 'action.execute' and trainer is not None:
        episode.experiences[-1].manual_execution = env.action_space.action2onehot(message['action'])
        episode.add_manual_execution()


# -------------------------------------------------- Inits etc.  ------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------

# TODO - OPEN ISSUES:
'''
# state vector normalizing
# in-page learning (?!)***
'''

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
rabbitMQ.queues.append({'name': 'storyteller', 'exchange': 'main', 'key': 'action.execute', 'callback': callback_action})

rabbitMQ.setup_queues()
rabbitMQ.start_consume()

