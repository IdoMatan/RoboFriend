import cv2
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
import os
# import subprocess
import vlc
import time
import sys
import PyQt5

# import pyqtgraph as pg


def draw_gaze(image_in, eye_pos, pitchyaw, length=200, thickness=1, color=(0, 0, 255)):
    """Draw gaze angle on given image with a given eye positions."""
    image_out = image_in
    if len(image_out.shape) == 2 or image_out.shape[2] == 1:
        image_out = cv2.cvtColor(image_out, cv2.COLOR_GRAY2BGR)
        
    dx = -length * np.sin(pitchyaw[1])
    dy = -length * np.sin(pitchyaw[0])
    cv2.arrowedLine(image_out, tuple(np.round(eye_pos).astype(np.int32)),
                   tuple(np.round([eye_pos[0] + dx, eye_pos[1] + dy]).astype(int)), color,
                   thickness, cv2.LINE_AA, tipLength=0.5)
    return image_out


def convert_to_unit_vector(angles):
    x = -torch.cos(angles[:, 0]) * torch.sin(angles[:, 1])
    y = -torch.sin(angles[:, 0])
    z = -torch.cos(angles[:, 1]) * torch.cos(angles[:, 1])
    norm = torch.sqrt(x**2 + y**2 + z**2)
    x /= norm
    y /= norm
    z /= norm
    return x, y, z


def compute_angle_error(preds, labels):
    pred_x, pred_y, pred_z = convert_to_unit_vector(preds)
    label_x, label_y, label_z = convert_to_unit_vector(labels)
    angles = pred_x * label_x + pred_y * label_y + pred_z * label_z
    return torch.acos(angles) * 180 / np.pi


def normalize_face(landmarks, frame):
    # Adapted from imutils package
    left_eye_coord=(0.70, 0.35)
    
    lcenter = tuple([landmarks[0],landmarks[5]])
    rcenter = tuple([landmarks[1],landmarks[6]])
    
    gaze_origin = (int((lcenter[0]+rcenter[0])/2), int((lcenter[1]+rcenter[1])/2))

    # compute the angle between the eye centroids 
    dY = rcenter[1] - lcenter[1]
    dX = rcenter[0] - lcenter[0]
    angle = np.degrees(np.arctan2(dY, dX)) - 180

    # compute the desired right eye x-coordinate based on the
    # desired x-coordinate of the left eye
    right_eye_x = 1.0 - left_eye_coord[0]

    # determine the scale of the new resulting image by taking
    # the ratio of the distance between eyes in the *current*
    # image to the ratio of distance between eyes in the
    # *desired* image
    dist = np.sqrt((dX ** 2) + (dY ** 2))
    new_dist = (right_eye_x - left_eye_coord[0])
    new_dist *= 112
    scale = new_dist / dist

    # grab the rotation matrix for rotating and scaling the face
    M = cv2.getRotationMatrix2D(gaze_origin, angle, scale)

    # update the translation component of the matrix
    tX = 112 * 0.5
    tY = 112 * left_eye_coord[1]
    M[0, 2] += (tX - gaze_origin[0])
    M[1, 2] += (tY - gaze_origin[1])

    # apply the affine transformation
    face = cv2.warpAffine(frame, M, (112, 112),
        flags=cv2.INTER_CUBIC)
    return face, gaze_origin, M


def live_plot(xs, ys, plotWidget):
    # plt.figure()
    # plt.clf()
    # # plt.ion()
    # fig = plt.figure(figsize=(13, 6))
    # ax = fig.add_subplot(111)
    #
    if ys.__len__() > 20:
        xs = xs[-20:]
        ys = ys[-20:]
    # plt.plot(xs, ys)
    # # Format plot
    # # plt.xticks(rotation=45, ha='right')
    # # plt.subplots_adjust(bottom=0.30)
    # # plt.title('TMP102 Temperature over Time')
    # # plt.ylabel('Temperature (deg C)')
    # # plt.show(fig)
    # # plt.show(False)
    # plt.pause(0.0005)

    plotWidget.plot(xs, ys)


def attention(gaze):
    attention_score = np.sqrt(np.square(gaze[0].detach().cpu().numpy()) + np.square(gaze[1].detach().cpu().numpy()))
    attention_score = 1 - attention_score
    return attention_score


class PlayMovie:
    def __init__(self, pages=0, path=None):
        self.player = None if path is None else vlc.MediaPlayer(path)
        # self.pages_map = pages

    def choose_story(self, path):
        self.player = vlc.MediaPlayer(path)

    def play(self, position=0.0):
        self.player.set_fullscreen(b_fullscreen=True)

        self.player.play()

        self.player.set_time(position)

    def pause(self):
        self.player.pause()

    def stop(self):
        self. player.stop()

    def switch_story(self, path):
        self.player.stop()
        self.player = vlc.MediaPlayer(path)

    def play_page_with_pagemap(self, segment):
        if segment < len(self.pages_map):

            from PyQt5 import QtCore
            from PyQt5 import QtGui
            import sys

            vlcApp = QtGui.QGuiApplication(sys.argv)
            vlcWidget = vlcApp.QFrame()
            vlcWidget.resize(700, 700)
            vlcWidget.show()
            self.player.set_nsobject(vlcWidget.winId())

            duration_in_sec = self.pages_map[segment + 1] - self.pages_map[segment]
            self.play(position=self.pages_map[segment])
            print('Playing page:', segment, '/', len(self.pages_map))
            stopwatch(duration_in_sec)
            self.stop()
        else:
            self.play(position=self.pages_map[segment])
            print('Playing page:', segment, '/', len(self.pages_map))

    def play_page(self, start_position=0.0, stop_position=1.0):
        self.player.set_fullscreen(b_fullscreen=True)
        self.player.set_time(start_position*1000)
        self.player.play()

        # duration_in_sec = start_position - stop_position
        # stopwatch(duration_in_sec)
        # self.pause()
        return 0

    def get_time(self):
        return self.player.get_time()


def stopwatch(seconds):
    start = time.time()
    time.clock()
    elapsed = 0
    while elapsed < seconds:
        elapsed = time.time() - start
        time.sleep(0.2)

    return 1

#
# class VideoClock:
#     def __init__(self):
#         self.time_now = int(time.time()/1000)
#         self.alarm = None
#
#     def latch(self, duration):
#         self.alarm = self.time_now + duration
#
#     def update(self,):
#         self.time_now = int(time.time()/1000)
#         if self.alarm is not None and self.time_now >= self.alarm:
#             self.alarm = None
#             return 1
#         else:
#             return 0
