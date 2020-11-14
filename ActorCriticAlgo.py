import torch.optim as optim
from torch.autograd import Variable
from utils import *
import time
import sys, os
import json
import logging
from ResNet import *
from datetime import datetime, timezone

# TODO make hyperparameters as a json_config file? not sure needed
hidden_size = 256
learning_rate = 3e-5

# Constants
GAMMA = 0.99
num_steps = 1000
max_episodes = 1


class ActorCritic(nn.Module):
    def __init__(self, num_inputs, num_actions, hidden_size, learning_rate=3e-4):
        super(ActorCritic, self).__init__()

        self.num_actions = num_actions
        self.num_actions = num_actions
        self.critic_linear1 = nn.Linear(num_inputs, hidden_size)
        self.critic_linear2 = nn.Linear(hidden_size, 1)

        self.actor_linear1 = nn.Linear(num_inputs, 128)
        self.actor_linear2 = nn.Linear(128, hidden_size)
        self.actor_linear3 = nn.Linear(hidden_size, num_actions)

        self.resnet = ResNet18(num_classes=10)

    def forward(self, state):
        state = np.array(state)
        state = Variable(torch.from_numpy(state).float().unsqueeze(0))

        value = F.relu(self.critic_linear1(state))
        value = self.critic_linear2(value)

        policy_dist = F.relu(self.actor_linear1(state))
        policy_dist = F.relu(self.actor_linear2(policy_dist))
        policy_dist = F.softmax(self.actor_linear3(policy_dist), dim=1)

        return value, policy_dist


class Trainer:
    def __init__(self, n_actions, state_len, params=None, manual=False):
        self.n_actions = n_actions
        self.state_len = state_len
        self.actor_critic = None
        self.optimizer = None
        self.episode = 0
        self.diff_constraints_module = None
        self.manual = manual
        self. ltl_reward = None
        self. ltl_reward_terminal = None

    def load_a2c(self, load=False):
        num_inputs = self.state_len
        num_outputs = self.n_actions

        if load:
            loaded = torch.load('robofriend_model.pth')
            actor_critic = loaded['model']
            actor_critic.load_state_dict(loaded['model_state_dict'])
            ac_optimizer = optim.Adam(actor_critic.parameters(), lr=learning_rate)
            ac_optimizer.load_state_dict(loaded['optimizer_state_dict'])
            self.episode = loaded['episode'] + 1
        else:
            actor_critic = ActorCritic(num_inputs, num_outputs, hidden_size)
            ac_optimizer = optim.Adam(actor_critic.parameters(), lr=learning_rate)

        self.actor_critic, self.optimizer = actor_critic, ac_optimizer

        return actor_critic, ac_optimizer

    def train(self, episode, last_state):
        Qval_final, _ = self.actor_critic.forward(last_state)
        Qval_final = Qval_final.detach().numpy()[0, 0]
        Qvals = episode.compute_Qvals(Qval_final)

        # update actor critic
        values = torch.FloatTensor(episode.values)
        Qvals = torch.FloatTensor(Qvals)

        log_probs = torch.FloatTensor(episode.log_probs)

        action_output = torch.stack(episode.policy_dist)

        advantage = Qvals - values
        diff_constraints_loss_vec = torch.stack(episode.diff_constraints)
        # TODO - look at dimensions and add it to actor loss (didn't do it yet just to align dimensions before)
        actor_loss = (-log_probs * advantage).mean()
        critic_loss = 0.5 * advantage.pow(2).mean()
        if self.manual:
            action_manual = torch.stack(episode.manual_executions)
            ac_loss = imitation_loss(action_output=action_output, action_manual=action_manual) + torch.mean(diff_constraints_loss_vec)  # Test if needed
        else:
            ac_loss = actor_loss + critic_loss + 0.001 * episode.entropy + torch.mean(diff_constraints_loss_vec)

        self.optimizer.zero_grad()
        ac_loss.backward()
        self.optimizer.step()
        return {'actor_loss': float(actor_loss.detach()), 'critic_loss': float(critic_loss.detach()),
                'ac_loss': float(ac_loss.detach())}

    def save_model(self, filename='robofriend_model.pth'):
        torch.save({'model': self.actor_critic,
                    'model_state_dict': self.actor_critic.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'episode': self.episode}, filename)


class DiffConstraints_loss:
    ''' An loss module based on linear temporal logic - ADD DESCRIPTION HERE '''
    def __init__(self):
        self.losses = []
        self.weights = []

        self.implemeted_losses = [diff_constraints_diversity, diff_constraints_do_not_repeat]

    def add_constraint(self, loss):
        '''
        append a loss function to be calculated as part of the diff_constraints loss
        :param loss: an diff_constraints loss function
        '''
        assert (loss not in self.implemeted_losses, 'Loss not implemented')
        self.losses.append(loss)

    def loss(self, state, action_vec):
        '''
        :param state: torch vector with state vector (see reward function for details)
        :param action_vec: log probs of actions (output of network)
        :return: accumulated loss from losses in self.losses
        '''
        acc_loss = 0
        for loss in self.losses:
            acc_loss += loss(state, action_vec)
        return acc_loss


def diff_constraints_diversity(state_input, action_output):
    # TODO - add description
    action_weights = torch.tensor((0.4, 0.2, 0.2, 0.2))
    return torch.sum(state_input[11:15]*action_output*action_weights)


def diff_constraints_do_not_repeat(state_input, action_output):
    # TODO - add description
    return torch.sum(state_input[7:11]*action_output)


def imitation_loss(action_output, action_manual):
    return torch.mean((action_output - action_manual)**2)


class Actions:
    def __init__(self, config):
        self.n = len(config)
        self.action_string = config

    def action(self, x):
        return self.action_string[x]  # if n=10, action # 2 would be 0.2 (throttle value)

    def action2onehot(self, action):
        onehot = torch.zeros(self.n)
        for i in range(self.n):
            if action == self.action_string[i]:
                onehot[i] = 1
                return onehot


class Environment:
    def __init__(self):

        self.reward = None
        self.state = None
        self.action_space = None
        self.story = None
        self.user = None
        self.session_uid = None
        self.state_buffer = StateBuffer()
        self.mic_buffer = MicBuffer()
        self.prev_action = [4, 4, 0]
        self.accumulated_actions = None

        # LTL init
        per_page_formula, terminal_formula = RewardLTL.load_constraints_json('../LTL_constraints.json')
        self.ltl_reward = RewardLTL(per_page_formula, dfa=False)
        self.ltl_reward_terminal = RewardLTL(terminal_formula, dfa=False)

    def update(self, story_name, story_config, user='admin', session=np.random.randint(0, 1000)):
        self.reward = 0
        self.action_space = Actions(story_config['actions'])
        self.story = story_name
        self.user = user
        self.session_uid = session
        self.accumulated_actions = torch.zeros(self.action_space.n)

    def reset(self):
        self.mic_buffer.reset()
        self.state_buffer.reset()
        return True

    def step(self):
        self.state = self.get_state_vec()

        # reward = self.calc_reward()
        is_done = 0  # unknown at this stage

        # return self.state, reward, is_done
        return self.state, is_done

    def calc_reward(self):
        # state vector structure:
        # 0=page, 1= n_kids, 2=attention, 3=excitation, 4=volume, 5=sound_diff, 6=prev_action,
        # 7-10=prev_action as one-hot, 11-14= accumulated prev actions as one-hot, 15-17= last 3 actions
        ltl_reward_mag = 10
        ltl_state = self.ltl_reward.parse_action(self.state[-3:].detach().tolist())

        ltl_reward = ltl_reward_mag if self.ltl_reward.truth(ltl_state) else 0

        reward = (self.state[2] - self.state[3] - self.state[4] + self.state[5]) + ltl_reward

        return reward

    def get_state_vec(self):
        state_vec = self.state_buffer.accumulated_state(self.prev_action[-1])
        self.state_buffer.previous_action = self.prev_action[-1]
        one_hot_action = torch.zeros(self.action_space.n)
        one_hot_action[int(state_vec[6])] = 1
        self.accumulated_actions += one_hot_action

        state_vec = torch.cat((state_vec.float(),                           # original state vector
                               one_hot_action,                              # Last action as one-hot
                               self.accumulated_actions,                    # accumulated one-hot actions
                               torch.FloatTensor(self.prev_action[-3:])))   # last 3 actions as ints for LTL

        return state_vec


class Episode:
    def __init__(self, session_id, logger_name):
        self.uuid = session_id
        self.timestamp = time.time()
        self.experiences = []
        self.logger = logger_name
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.story_name = None
        self.entropy = 0
        self.diff_constraints = []
        self.ltl_reward = {}
        self.ltl_reward_terminal = {}
        self.manual_executions = []
        self.policy_dist = []

    def add_experience(self, experience, log=True):
        self.experiences.append(experience)
        self.rewards.append(experience.reward)
        self.values.append(experience.value)
        self.log_probs.append(experience.log_probs)
        self.policy_dist.append(experience.policy_dist)

        if log:
            self.log(experience)

    def add_manual_execution(self, log=True):
        self.manual_executions.append(self.experiences[-1].manual_execution)
        if log:
            self.log(self.experiences[-1])

    def log(self, experience):
        self.logger.info(json.dumps(experience.as_dict()))

    def __len__(self):
        return len(self.experiences)

    def compute_Qvals(self, Qval, GAMMA=0.99):
        Qvals = np.zeros_like(self.values)
        for t in reversed(range(len(self.rewards))):
            Qval = self.rewards[t] + GAMMA * Qval
            Qvals[t] = Qval
        return Qvals

    def export(self):
        # save as numpy/pytorch/...
        pass


class Experience:
    def __init__(self, episode, state, action, reward, next_state, value, log_probs, policy_dist):
        self.episode = episode
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.value = value
        self.log_probs = log_probs
        self.policy_dist = policy_dist
        self.manual_execution = None

    def as_dict(self):
        return {'episode': self.episode,
                'state': list(self.state),
                'action': self.action,
                # 'reward': float(torch.round(self.reward * 10**2) / (10**2)),
                'reward': float(round(self.reward)),
                'next_state': self.next_state,
                'value': float(round(self.value, 3))}


class StateBuffer:
    ''' Used to temporary buffering of metrics from mic and cam, later accumlated to form a state vec '''
    def __init__(self):
        self.dict_keys = {'page': 0, 'n_kids': 1, 'attention': 2, 'excitation': 3, 'volume': 4, 'sound_diff': 5, 'prev_action': 6}
        self.states = np.empty((0, len(self.dict_keys.keys())), float)
        self.previous_action = 0

    def add_state(self, page, n_kids, attention, excitation, volume, sound_diff, prev_action):
        if prev_action == 'auto':
            prev_action = self.previous_action
        self.states = np.vstack((self.states, [page, n_kids, attention, excitation, volume, sound_diff, prev_action]))

    def get_metric(self, key):
        if key in self.dict_keys.keys():
            return self.states[:, self.dict_keys.get(key)]

    def accumulated_state(self, prev_action):
        ''' Return an accumlated state vec from the metrics gathered since last reset '''
        temp_state = np.mean(self.states, axis=0)
        temp_state[self.dict_keys['prev_action']] = prev_action
        return torch.from_numpy(temp_state)

    def format_as_log_message(self, state_vec):
        ''' Format as dictionary object to send over RabbitMQ '''
        utc_dt = datetime.now(timezone.utc)  # UTC time
        time_stamp = utc_dt.strftime('%Y-%m-%d %H:%M:%S')

        if len(state_vec) <= 8:   # case of pure metrics - before action taken
            state_as_dict = dict(zip(self.dict_keys.keys(), state_vec.tolist()))
            state_as_dict.update({'time': time_stamp})
        else:                     # case of state-action log (after inference)
            state_as_dict = dict(zip(self.dict_keys.keys(), state_vec[0:len(self.dict_keys.keys())].tolist()))
            state_as_dict.update({'action_prev1': int(state_vec[15]),
                                  'action_prev2': int(state_vec[15]),
                                  'action_prev3': int(state_vec[15]),
                                  'time': time_stamp})
        return state_as_dict

    def reset(self):
        self.states = np.empty((0, len(self.dict_keys.keys())), float)


class MicBuffer:
    def __init__(self):
        self.volume = []
        self.noise_diff = []

    def append(self, volume, noise_diff):
        self.volume.append(volume)
        self.noise_diff.append(noise_diff)

    def reset(self):
        self.volume = []
        self.noise_diff = []

    def get_avg(self, key):
        if key == 'volume':
            return np.mean(self.volume) if len(self.volume) else 0
        elif key == 'noise_diff':
            return np.mean(self.noise_diff) if len(self.volume) else 0
        else:
            print('error - non-existing key')


# class PageExperience:
#     def __init__(self, page, episode):
#         self.page = page
#         self.episode = episode
#         self.states = []
#
#     def __getitem__(self, item):
#         return self.states[item]
#
#     def append_state(self, new_state):
#         self.states.append(new_state)
#
#     def page_summary(self):
#         return self.states[-1]

#
# def calc_reward(state):
#
#     reward = 100
#     is_done = 0
#
#     return reward, is_done


def setup_logger(name, dir_name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    # formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')
    formatter = logging.Formatter(
        '{"time":"%(asctime)s", "name": "%(name)s","level": "%(levelname)s", "message": %(message)s}')
    if not os.path.exists(f'./{dir_name}/'):
        os.makedirs(f'./{dir_name}/')

    log_file = './' + dir_name + '/' + log_file

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
