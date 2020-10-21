from flloat.parser.ltlf import LTLfParser
import time
import json


class RewardLTL:
    '''
    LTL module to use as part of an RL reward - simple implementation
    formula_str should be an LTL statement string (e.g. 'F(play)' meaning eventually state should be play
     '''
    def __init__(self, formula_str, dfa=False):
        self.parser = LTLfParser()
        self.formula_string = formula_str
        self.ltl = self.parser(self.formula_string)
        if dfa:
            self.dfa = self.ltl.to_automaton()
        else:
            self.dfa = None

    def truth(self, state_trace, dfa=False):
        '''
        :param state_trace: a list of dict objects, each describing a state (e.g. {'ask_question': True}
        :param dfa: set to true to check using a symbolic dfa
        :return: True if ltl formula accepts trace, false otherwise
        '''
        if not dfa:
            return self.ltl.truth(state_trace)
        else:
            if not self.dfa:
                self.dfa = self.ltl.to_automaton()
            return self.dfa.accepts(state_trace)

    @staticmethod
    def parse_action(num):
        '''
        Convert action num to ltl state dict shape {string: bool}
        :param num: action number (from 0 to 3 currently)
        :return: dict{action_as_string: True}
        '''
        assert num <= 3, 'Only 4 possible actions!'
        preset = ["play_next_page", "wave_hands", "move_head", "ask_question"]
        return {preset[num]: True}
        # return dict(zip(preset, [True if i == num else False for i in range(4)]))

    @staticmethod
    def load_constraints_json(filename):
        with open(filename) as json_file:
            constraints = json.load(json_file)

        per_action = constraints['per_action']
        terminal = constraints['terminal']
        print('Per action LTL constraint:', per_action['description'])
        print('Terminal reward LTL constraint:', terminal['description'])

        return per_action['formula'], terminal['formula']


# --------------------------------------------------------------------------------------------------------------

# ltl_formula = "G(ask_question -> X !ask_question) & G(wave_hands -> X !wave_hands) & F(ask_question)"

per_page_formula, terminal_formula = RewardLTL.load_constraints_json('LTL_constraints.json')

ltl_reward = RewardLTL(per_page_formula)   # init module
ltl_reward_terminal = RewardLTL(terminal_formula)   # init module

state_trace = [ltl_reward.parse_action(0),
               ltl_reward.parse_action(1),
               ltl_reward.parse_action(1),
               ltl_reward.parse_action(3),
               ltl_reward.parse_action(2)]

print('States Trace:', *state_trace, sep='\n')

start = time.time()
print('\nLTL per action acceptance:', ltl_reward.truth(state_trace))
print('\nLTL terminal acceptance:', ltl_reward_terminal.truth(state_trace))

print('Elapsed time:', round(abs(time.time()-start)*1000, 4), 'ms')
