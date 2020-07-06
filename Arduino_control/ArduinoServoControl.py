# servo control 15.12.2016

# 1) user set servo position in python
# 2) position is sent to arduino
# 3) arduino moves servo to position
# 4) arduino send confirmation message back to python
# 5) message is printed in python console

import serial  # import serial library
# import pyserial as serial  # import serial library
import time


class ServoControl:
    # def __init__(self, port='/dev/ttyACMO', baudrate=9600, start_angle=0):
    # def __init__(self, port='/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_955303436343511130D1-if00', baudrate=9600, start_angle=0):
    # def __init__(self, port='/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_757363032363515030D1-if00', baudrate=9600, start_angle=0):
    def __init__(self, port='/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_85734323730351803101-if00', baudrate=9600, start_angle=0):
        self.arduino = serial.Serial(port, baudrate)  # create serial object named arduino
        # self.current_angle = start_angle
        self.set_servo_angle()
        time.sleep(3)

        print('Servo initialized')

    def set_servo_angle(self, roll=50, pitch=50, left=25, right=25):
        # angle = str(roll) + ',' + str(pitch) + '\n'
        angle = str(roll) + 'r' + str(pitch) + 'p' + str(left) + 'l' + str(right) + '\n'
        self.arduino.write(angle.encode())                    # write position to serial port
        print('sent roll angle to servo:', roll)
        print('sent pitch angle to servo:', pitch)
        print('sent left angle to servo:', left)
        print('sent right angle to servo:', right)

        # if self.read_servo_angle() is None:
        #     return 0
        # else:
        #     self.current_angle = angle
        #     return 1

    def read_servo_angle(self):
        position = None
        # position = str(self.arduino.readline())      # read serial port for arduino echo
        # print('Servo location:', position)
        return position

    def execute_action(self, action, dtheta):
        new_angle = self.current_angle + -1*(action - 1) * dtheta   # action=0 is left, action=1 is stay, action=2 is right
        if 0 <= new_angle <= 180:
            self.set_servo_angle(new_angle)
            self.current_angle = new_angle
        else:
            self.set_servo_angle(self.current_angle)
        # print(new_angle)

    def test_mode(self, mode=1):
        delta = 5 * mode
        if mode == -1:
            start = 45
            stop = 135
        else:
            start = 135
            stop = 45

        for angle in range(start, stop, delta):
            angle2 = angle
            self.set_servo_angle(roll=90, pitch=angle)
            time.sleep(0.05)


def test_run(delta):
    servo = ServoControl()
    max_angle = 100

    for i in range(1, 5):
    #     for angle in range(1, max_angle, delta):
    #         servo.set_servo_angle(roll=angle, pitch=50, left=angle, right=angle)
    #         time.sleep(0.2)
    #
    # for i in range(1, 5):
    #     for angle in range(1, max_angle, delta):
    #         angle2 = angle
    #         servo.set_servo_angle(roll=50, pitch=angle, left=angle, right=angle)
    #         time.sleep(0.2)

    # servo.set_servo_angle()

        servo.set_servo_angle(roll=50, pitch=50)  # , left=25, right=50)
        time.sleep(3)

        servo.set_servo_angle(roll=10, pitch=10)  # , left=1, right=1)
        time.sleep(3)

        servo.set_servo_angle(roll=50, pitch=50)
        time.sleep(3)

        servo.set_servo_angle(roll=90, pitch=90)
        time.sleep(3)

    servo.set_servo_angle(roll=50, pitch=50)
    time.sleep(3)
        # time.sleep(0.5)

        # servo.set_servo_angle(roll=70, pitch=110)
        # time.sleep(3)
        # time.sleep(0.5)
        #
        # servo.set_servo_angle(roll=10, pitch=10, left=20, right=20)
        # time.sleep(5)


test_run(10)
