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
    def __init__(self, port='/dev/serial/by-id/usb-Arduino_Srl_Arduino_Uno_955303436343511130D1-if00', baudrate=9600, start_angle=0):
        self.arduino = serial.Serial(port, baudrate)  # create serial object named arduino
        self.current_angle = start_angle
        self.set_servo_angle(self.current_angle)
        print('Servo initialized')

    def set_servo_angle(self, angle1, angle2=0):
        angle = str(angle1) + ',' + str(angle2) + '\n'
        self.arduino.write(angle.encode())                    # write position to serial port
        print('sent angle 1 to servo:', angle1)
        print('sent angle 2 to servo:', angle2)

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


def test_run(delta):
    servo = ServoControl()
    angle = 0
    max_angle = 180
    for angle in range(0, max_angle, delta):
        angle2 = 0
        servo.set_servo_angle(angle2, angle)
        time.sleep(0.5)

# test_run(5)