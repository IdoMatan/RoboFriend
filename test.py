import pyboard
import time


pyb = pyboard.Pyboard('/dev/cu.usbserial-0001', 115200)
pyb.enter_raw_repl()

ledstate = False
for i in range(10):

    ret = pyb.exec(f'led.value({ledstate})')
    ledstate = not ledstate
    print(ret)
    time.sleep(0.2)

pyb.exit_raw_repl()

