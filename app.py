import tkinter as tk
import pandas as pd
from time import strftime
from PIL import Image, ImageTk


# simply place it in the same folder as this script and it will import the Flight_Bot class

def caps_from(event):
    """Forces the input FROM to be upper case and less than 4 characters"""

    story_name.set(story_name.get().upper())
    if len(story_name.get()) > 10: story_name.set(story_name.get()[:10])


def caps_to(event):
    """Forces the input TO to be upper case and less than 4 characters"""

    username.set(username.get().upper())
    if len(username.get()) > 10: username.set(username.get()[:10])


def close_app():
    window.destroy()


def run_app():
    print('Playing the story man')
    labelText.set('Playing....')
    status.update()
# ------------------------------------------------------------------------------------------------------------

window = tk.Tk()  # you may also see it named as "root" in other sources

window.title("RoboBear App")  # self explanatory!
# window.geometry("600x600") # size of the window when it opens
# window.minsize(width=600, height=600) # you can define the minimum size of the window like this
window.resizable(width="false", height="false")  # change to false if you want to prevent resizing

# window.iconbitmap('assets/logo.icns')


# three frames on top of each other
frame_header = tk.Frame(window, borderwidth=2, pady=2)
center_frame = tk.Frame(window, borderwidth=2, pady=5)
bottom_frame = tk.Frame(window, borderwidth=2, pady=5)
status_frame = tk.Frame(window, borderwidth=2, pady=5)
picture_frame = tk.Frame(window, borderwidth=2, pady=5)

frame_header.grid(row=0, column=0)
center_frame.grid(row=1, column=0)
bottom_frame.grid(row=2, column=0)
status_frame.grid(row=3, column=0)
picture_frame.grid(row=4, column=0)

# status text
labelText = tk.StringVar()
labelText.set('Press Play to start')

# picture

load = Image.open("./assets/bearpic.jpg")
load = load.resize((100, 100), Image.ANTIALIAS)
render = ImageTk.PhotoImage(load)
img = tk.Label(picture_frame, image=render)
img.image = render


# label header to be placed in the frame_header
header = tk.Label(frame_header, text="RoboBear Controller Gui", bg='white', fg='black', height='3', width='50',
                  font=("Helvetica 16 bold"))

status = tk.Label(status_frame, textvariable=labelText, bg='white', fg='green', height='3', width='50',
                  font=("Helvetica 12 bold"))

# inside the grid of frame_header, place it in the position 0,0
header.grid(row=0, column=0)
status.grid(row=3, column=0)

# two additional frames go inside the center_frame
frame_main_1 = tk.Frame(center_frame, borderwidth=2, relief='sunken')
frame_main_2 = tk.Frame(center_frame, borderwidth=2, relief='sunken')

# populate the frames with the labels referring to the inputs we want from the user
story = tk.Label(frame_main_1, text="Choose Story:      ")
user = tk.Label(frame_main_2, text="Enter username:      ")

# Put it simply: StringVar() allows you to easily track tkinter variables and see if they were read, changed, etc
# check resources here for more details: http://effbot.org/tkinterbook/variable.htm
story_name = tk.StringVar()
username = tk.StringVar()


# creating the entries for the user input, FROM, TO and dates
story_entry = tk.Entry(frame_main_1, textvariable=story_name, width=20)
story_entry.bind("<KeyRelease>",
                     caps_from)  # everytime a key is released, it runs the caps_from function on the cell

username_entry = tk.Entry(frame_main_2, textvariable=username, width=20)
username_entry.bind("<KeyRelease>", caps_to)  # everytime a key is released, it runs the caps_to function on the cell

# and we pack the two frames in the center_frame and then the elements inside them
frame_main_1.pack(fill='x', pady=2)
frame_main_2.pack(fill='x', pady=2)
#
# the order which we pack the items is important
story.pack(side='left')
story_entry.pack(side='right', padx=20)
user.pack(side='left')
username_entry.pack(side='right', padx=20)
img.pack()

# a proper app needs some buttons too!
button_run = tk.Button(bottom_frame, text="Play", command=run_app, bg='dark green', fg='white', relief='raised',
                       width=10, font=('Helvetica 9 bold'))
button_run.grid(column=0, row=0, sticky='w', padx=100, pady=2)

button_close = tk.Button(bottom_frame, text="Exit", command=close_app, bg='dark red', fg='white', relief='raised',
                         width=10, font=('Helvetica 9'))
button_close.grid(column=1, row=0, sticky='e', padx=100, pady=2)

window.mainloop()
