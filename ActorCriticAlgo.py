import torch.optim as optim
from torch.autograd import Variable
from utils import *
import time
import sys, os
import json
import logging
from ResNet import *


# TODO make hyperparameters as a json_config file
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
    def __init__(self, n_actions, state_len, params=None):
        self.n_actions = n_actions
        self.state_len = state_len
        self.actor_critic = None
        self.optimizer = None
        self.episode = 0

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
        log_probs = torch.stack(episode.log_probs)

        advantage = Qvals - values
        actor_loss = (-log_probs * advantage).mean()
        critic_loss = 0.5 * advantage.pow(2).mean()
        ac_loss = actor_loss + critic_loss + 0.001 * episode.entropy

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


class Actions:
    def __init__(self, config):
        self.n = len(config)
        self.action_string = config

    def action(self, x):
        return self.action_string[x]  # if n=10, action # 2 would be 0.2 (throttle value)


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

    def update(self, story_name, story_config, user='admin', session=np.random.randint(0, 1000)):

        self.reward = 0
        self.action_space = Actions(story_config['actions'])
        self.story = story_name
        self.user = user
        self.session_uid = session

    def reset(self):
        self.mic_buffer.reset()
        self.state_buffer.reset()
        return True

    def step(self):
        self.state = self.state_buffer.accumulated_state()
        reward = self.calc_reward()
        is_done = 0  # unknown at this stage

        return self.state, reward, is_done

    def calc_reward(self):
        reward = 100

        return reward


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

    def add_experience(self, experience, log=True):
        self.experiences.append(experience)
        self.rewards.append(experience.reward)
        self.values.append(experience.value)
        self.log_probs.append(experience.log_probs)
        if log:
            self.log(experience)

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
    def __init__(self, episode, state, action, reward, next_state, value, log_probs):
        self.episode = episode
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.value = value
        self.log_probs = log_probs

    def as_dict(self):
        return {'episode': self.episode,
                'state': list(self.state),
                'action': self.action,
                'reward': float(round(self.reward, 2)),
                'next_state': self.next_state,
                'value': float(round(self.value, 3))}


class StateBuffer:
    def __init__(self):
        self.dict_keys = {'page': 0, 'n_kids': 1, 'attention': 2, 'excitation': 3, 'volume': 4, 'sound_diff': 5, 'prev_action': 6}

        self.states = np.empty((0, len(self.dict_keys.keys())), float)

    def add_state(self, page, n_kids, attention, excitation, volume, sound_diff, prev_action):
        if prev_action == 'auto':
            prev_action = 0
        self.states = np.vstack((self.states, [page, n_kids, attention, excitation, volume, sound_diff, prev_action]))

    def get_metric(self, key):
        if key in self.dict_keys.keys():
            return self.states[:, self.dict_keys.get(key)]

    def accumulated_state(self):
        return np.mean(self.states, axis=0)   # TODO - change to some other augmentation of state matrix?

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


class PageExperience:
    def __init__(self, page, episode):
        self.page = page
        self.episode = episode
        self.states = []

    def __getitem__(self, item):
        return self.states[item]

    def append_state(self, new_state):
        self.states.append(new_state)

    def page_summary(self):
        return self.states[-1]


def calc_reward(state):

    reward = 100
    is_done = 0

    return reward, is_done


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
