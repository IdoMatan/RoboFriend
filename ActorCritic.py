from torch.autograd import Variable
from utils import *
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


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
    def __init__(self, env, params=None):
        self.env = env
        self.actor_critic = None
        self.optimizer = None
        self.episode = 0

    def load_a2c(self, load=False):
        num_inputs = len(self.env.state)
        num_outputs = self.env.action_space.n

        if load:
            loaded = torch.load('robot_model.pth')
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

    def train(self, episode, last_state, entropy_term):
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
        ac_loss = actor_loss + critic_loss + 0.001 * entropy_term

        self.optimizer.zero_grad()
        ac_loss.backward()
        self.optimizer.step()
        self.update_planning_smoothness(episode)
        return {'actor_loss': float(actor_loss.detach()), 'critic_loss': float(critic_loss.detach()), 'ac_loss': float(ac_loss.detach())}

    def save_model(self, filename='robot_model.pth'):
        torch.save({'model': self.actor_critic,
                    'model_state_dict': self.actor_critic.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'episode': self.episode}, filename)


class Actions:
    def __init__(self, n):
        self.n = n

    def action(self, x):
        if x == 1:
            return 'read'
        else:
            return x


class Environment:
    def __init__(self, init_pose, drone, car, planner, goals, n_actions=10):

        self.reward = 0
        self.state = None
        self.action_space = Actions(n_actions)
        self.drone = drone
        self.drone_current_position = init_pose
        self.car = car
        self.car_current_position = init_pose
        self.planner = planner
        self.goals = [(round(goal[1],2), round(goal[0],2)) for goal in goals]
        self.current_goal = self.goals.pop(0)
        self.drone.current_goal = self.current_goal
        self.dt = 0

    def reset(self, pose, yaw_car, yaw_drone=0, offset_car=(0, 0), offset_drone=(0, 0)):
        self.drone.move(pose, yaw=yaw_drone, offset_x=offset_drone[0], offset_y=offset_drone[1])
        self.car.move(pose, yaw=yaw_car, offset_x=offset_car[0], offset_y=offset_car[1])

        self.state = self.get_state()
        return self.state

    def step(self, action, delay):

        self.drone.set_speed(action)
        self.dt += 1
        time.sleep(delay)
        self.state = self.get_state()

        if self.drone.dist(self.current_goal) < 2:

            if len(self.goals):
                self.current_goal = self.goals.pop(0)
                self.drone.current_goal = self.current_goal
                done = False
                reward, done = self.calc_reward(done, milestone=True)
                print('===========>>>  Flying to next goal:', self.current_goal)
            else:
                done = True
                reward, done = self.calc_reward(done, milestone=True)
                print('===========>>>  Reached destination goal!:', self.current_goal)

        else:
            done = False
            reward, done = self.calc_reward(done, milestone=False)

        return self.state, reward, done, None

    def calc_reward(self, is_done, milestone):

        reward = -self.dt    # accumulating penalty

        reward -= (self.state[0] + self.state[1]/10 + self.state[2])  # Penalty for relative metrics
        reward += self.state[3]/10  # reward for drone speed

        if not self.state[-1]:  # No line-of-sight penalty
            reward -= 50
        if milestone:           # reached a milestone reward
            reward += 50
        if is_done:
            if self.state[0] <= 2:   # vehicle also reached final destination
                reward += 200
            else:
                reward += 50
                is_done = False

        return reward, is_done

    def get_state(self):
        state_vec, state_dict = get_state_vector(self.drone, self.car, self.planner)

        self.drone.update_pose(state_dict['drone']['pose'])
        self.car.update_pose(state_dict['car']['pose'])
        self.car.update_pose(state_dict['car']['pose'])

        # Update relative heading:
        relative_angle = calc_relative_heading(self.drone.heading, self.car.heading)
        state_vec[2] = log(relative_angle) if relative_angle > 0 else relative_angle

        print(f' ->>>>> Drone position: {self.drone.current_pose}, heading: {self.drone.heading}')
        print(f' ->>>>> Car positione: {self.car.current_pose}, heading: {self.car.heading}, realtive: {relative_angle}')
        return state_vec


class Episode:
    def __init__(self, uuid, logger_name):
        self.uuid = uuid
        self.timestamp = time.time()
        self.experiences = []
        self.logger = logger_name
        self.rewards = []
        self.values = []
        self.log_probs = []

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
    def __init__(self, state, action, reward, next_state, value, log_probs, episode, drone_pose, car_pose):
        self.episode = episode
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.value = value
        self.log_probs = log_probs
        self.drone_pose = drone_pose
        self.car_pose = car_pose

    def as_dict(self):
        return {'episode': self.episode,
                'state': self.state,
                'action': self.action,
                'reward': float(round(self.reward, 2)),
                'next_state': self.next_state,
                'value': float(round(self.value, 3)),
                'drone_pose': self.drone_pose.tolist(),
                'car_pose': self.car_pose.tolist()}
