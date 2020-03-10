# Main Process for BearFriend operation
import multiprocessing
import utils
from VLC_app import *
import sys

'''
1. Run test script making sure all peripherals are connected and working
2. Start camera and servos - log number of kids + average noise level
3. Start playing story-video according to script vector (timestamps to stop at) - separate thread or process
4. @ 1-Hz do:
    a. Calculate average gaze
    b. Measure noise level
    c. Log to DB
5. When page is finished do:
    a. Calculate next action and reward
    b. Log experience (State, action, reward, next state)
6. Execute action and go to next page
'''

page_break_down = [0, 82, 159, 229, 310, 380, 466]


app = QApplication(sys.argv)
player = Player()
player.show()
player.resize(640, 480)

player.OpenFile('Videos/video_part1.mp4')

page = 1

session_number = 1
# ----------------------------------------------------------------------------------------------------------------
# Run test script to test devices etc.

# ----------------------------------------------------------------------------------------------------------------

cam.init()
mic.init()
state_log = []
experience = []

while button:
    state_log.append(get_state(cam, mic, video))

    if state_log[-1].video in [page_done, book_done]:
        state = calc_state(state_log)
        reward = calc_reward(state)
        action = calc_action(state, reward)
        experience.append([state, reward, action])
        log_experience_to_db(experience[-1])

        if state_log[-1].video == book_done:
            log_episode_to_db(experience)
            break
        else:
            execute_action(action)
            state_log = []

    time.sleep(1)







sys.exit(app.exec_())
