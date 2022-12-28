import tkinter as tk
from PIL import Image, ImageTk
import json
import atexit
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime
import services.init_services as init
import time
import threading

# ---------------------------------------------- RabbitMQ setup -------------------------------------------------------

enable_print = False
pre_defined_index = 0


def callback_action(method, properties, body, mode):
    global pre_defined_index
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    message = json.loads(body)
    story = stories[story_playing.get()]
    if enable_print: print(" --> EoP Callback -> [x] %r" % message)
    if mode == 'manual':
        action_popup(f'Finished page {message["page"]}', stories[story_playing.get()]['actions'])
    elif mode == 'pre-defined':
        # send_pre_defined_action(stories[story_playing.get()]['pre_defined_actions'][message["page"]])
        # send_pre_defined_action(stories[story_playing.get()]['actions'][stories[story_playing.get()]['pre_defined_actions'][pre_defined_index]])
        send_pre_defined_action(story['actions'][story['pre_defined_actions'][pre_defined_index]])

rabbitMQ = RbmqHandler('app_service')
rabbitMQ.declare_exchanges(['main'])

rabbitMQ.queues.append({'name': 'action', 'exchange': 'main', 'key': 'action.get', 'callback': 'get'})
rabbitMQ.setup_queues()


# ---------------------------------------------------------------------------------------------------------------------

# def init_env():
#     try:
#         init.kafka()
#         init.services()
#         return True
#     except:
#         print('Failed services init')
#         return False


def close_app():
    # rabbitMQ.close()
    # init.terminate_subprocesses(processes)
    window.destroy()


def start_story(story):
    if enable_print: print('Playing story - ', story)
    story_playing.set(story)
    labelText.set(f'Playing {story}')
    play_pause.set('Pause')
    button_run.update()
    message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
               'action': 'initial_start',
               'story_name': story,
               'story': stories[story],
               'username': username.get(),
               'session': session.get(),
               # 'manual': manual.get()
               'manual': False if mode.get() == 'auto' else True
               }
    # rabbitMQ.channel.basic_publish(exchange='main', routing_key='app', body=json.dumps(message))
    rabbitMQ.publish(exchange='main', routing_key='app', body=message)
    button_story1['state'] = 'disabled'
    button_story2['state'] = 'disabled'
    if enable_print: print(" [x] Sent %r:%r" % ('app', message))


def playpause():
    ''' pausing and playing video '''
    if enable_print: print(play_pause.get())
    if play_pause.get() == 'Pause':
        play_pause.set('Resume')
        labelText.set('Paused')
        message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': 'pause', 'story': None}
        # rabbitMQ.channel.basic_publish(exchange='main', routing_key='app', body=json.dumps(message))
        rabbitMQ.publish(exchange='main', routing_key='app', body=message)
        if enable_print: print(" [x] Sent %r:%r" % ('app', message))
        return
    elif play_pause.get() == 'Resume':
        play_pause.set('Pause')
        labelText.set('Playing')
        message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': 'play', 'story': None}
        # rabbitMQ.channel.basic_publish(exchange='main', routing_key='app', body=json.dumps(message))
        rabbitMQ.publish(exchange='main', routing_key='app', body=message)
        if enable_print: print(" [x] Sent %r:%r" % ('app', message))
        return

# ---------------------------------------------------------------------------------------------------------------------


def action_popup(msg, actions):

    def action_func(act):
        if enable_print: print('Action choosen:', act)
        action_choosen.set(act)
        message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': act, 'story': None}
        # rabbitMQ.channel.basic_publish(exchange='main', routing_key='action.execute', body=json.dumps(message))
        rabbitMQ.publish(exchange='main', routing_key='action.execute', body=message)
        window.after(500, check_queue)
        popup.destroy()

    popup = tk.Tk()
    popup.wm_title("Choose Action")
    popup.minsize(width=100, height=200)
    label = tk.Label(popup, text=msg, font=("Helvetica 12 bold"))
    label.pack(side="top", fill="x", pady=10)
    buttons = []
    action_choosen = tk.StringVar()

    for action in actions:
        buttons.append(tk.Button(popup, text=action, command=lambda arg=action: action_func(arg)).pack())

    popup.mainloop()
    return action_choosen


def send_pre_defined_action(act):
    if enable_print: print('Action choosen:', act)
    message = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'action': act, 'story': None}
    rabbitMQ.publish(exchange='main', routing_key='action.execute', body=message)

# ---------------------------------------------------------------------------------------------------------------------

window = tk.Tk()  # you may also see it named as "root" in other sources

window.title("RoboBear App")  # self explanatory
# window.geometry("600x600") # size of the window when it opens
# window.minsize(width=600, height=600) # you can define the minimum size of the window like this
window.resizable(width="false", height="false")  # change to false if you want to prevent resizing

try:
    window.iconbitmap('assets/logo.icns')
except:
    if enable_print: print('Running on linux - no support for logo....')

# ------------------------------------------------- setup frames ------------------------------------------------------
frame_header = tk.Frame(window, borderwidth=2, pady=2)  # title of page
status_frame = tk.Frame(window, borderwidth=2, pady=2)  # Status
input_frame = tk.Frame(window, borderwidth=2, pady=2)  # check box for mode
stories_frame = tk.Frame(window, borderwidth=2, pady=2)  # buttons with story names
buttons_frame = tk.Frame(window, borderwidth=2, pady=2)  # picture of bear or anything we want

frame_header.grid(row=0, column=0)
status_frame.grid(row=1, column=0)
input_frame.grid(row=2, column=0)
stories_frame.grid(row=3, column=0)
buttons_frame.grid(row=4, column=0)


# -------------------------------------------------- Variables  -------------------------------------------------------
labelText = tk.StringVar()
play_pause = tk.StringVar()
username = tk.StringVar(value='admin')
session = tk.StringVar(value=str(int(time.time())))
manual = tk.BooleanVar(value=True)
mode = tk.StringVar(value='manual')

story_playing = tk.StringVar()

# test = tk.Variable()
# test.trace("w", callback_action)

labelText.set('Press on story to start session')
play_pause.set('Press on story')
manual.set(True)

# ------------------------------------------------- Load images -------------------------------------------------------

load = Image.open("./assets/foxstory.png")
load = load.resize((100, 100), Image.ANTIALIAS)
render = ImageTk.PhotoImage(load)
fox_img = render

load = Image.open("./assets/aptforrent.png")
load = load.resize((100, 100), Image.ANTIALIAS)
render = ImageTk.PhotoImage(load)
apt_img = render

# ------------------------------------------------- Set labels --------------------------------------------------------

header = tk.Label(frame_header, text="RoboBear Controller Gui", bg='white', fg='black', height='3', width='50',
                  font=("Comic Sans MS", "25", "bold"))

status = tk.Label(status_frame, textvariable=labelText, fg='blue', height='3', width='50',
                  font=("Helvetica 12 bold"))

# inside the grid of frame_header, place it in the position 0,0
header.grid(row=0, column=0)
status.grid(row=0, column=0)

session_label = tk.Label(input_frame, text="Session #: ")
user_label = tk.Label(input_frame, text="Username: ")

session_entry = tk.Entry(input_frame, textvariable=session, width=10)
username_entry = tk.Entry(input_frame, textvariable=username, width=10)

# checkbox = tk.Checkbutton(input_frame, text="Manual mode", variable=manual)
mode_list = tk.OptionMenu(input_frame, mode, "manual", "auto", "pre-defined")

# the order which we pack the items is important
user_label.pack(side='left')
username_entry.pack(side='left', padx=5)
# checkbox.pack(side='right', padx=5)
mode_list.pack(side='right', padx=5)
session_entry.pack(side='right', padx=5)
session_label.pack(side='right')

# ------------------------------------------------- Buttons -----------------------------------------------------------

button_story1 = tk.Button(stories_frame, image=apt_img, command=lambda: start_story('AptForRent'), bg='dark green', fg='white', relief='raised')
button_story2 = tk.Button(stories_frame, image=fox_img, command=lambda: start_story('FoxStory'), bg='dark green', fg='white', relief='raised')

button_story1.grid(column=1, row=0, sticky='e', padx=100, pady=2)
button_story2.grid(column=2, row=0, sticky='e', padx=100, pady=2)

button_run = tk.Button(buttons_frame, textvariable=play_pause, command=playpause, bg='dark green', fg='black', relief='raised',
                       width=10, font=('Helvetica 9 bold'))
button_run.grid(column=0, row=0, sticky='w', padx=100, pady=2)

button_close = tk.Button(buttons_frame, text="Exit", command=close_app, bg='dark red', fg='black', relief='raised',
                         width=10, font=('Helvetica 9'))
button_close.grid(column=1, row=0, sticky='e', padx=100, pady=2)


# ------------------------------------------------- Load Config file --------------------------------------------------


with open('StoryConfig.json') as json_file:
    stories = json.load(json_file)

# ------------------------------------------------- Init environment --------------------------------------------------

# processes = init.services()
#
# atexit.register(init.terminate_subprocesses, processes)


def check_queue():
    method, properties, body = rabbitMQ.pull_from_queue('action')
    if method is not None:
        message = json.loads(body)
        if message.get('manual'):
            callback_action(method, properties, body, mode=mode.get())

        else:
            if enable_print: print('Page ended --> Auto mode (algo chooses action)')
        if message.get('command') == 'end_of_story':
            if enable_print: print('Story ended --> Closing everything')
            print('\n-------------------------- STORY IS OVER! ------------------------------------\n')
            window.destroy()
            exit()

    window.after(500, check_queue)


window.after(500, check_queue)

window.mainloop()
