import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from rabbitmq.rabbitMQ_utils import *
from datetime import datetime
import time
import argparse

enable_print = False

def stopwatch(args):
    seconds = args.duration
    page = args.page
    start = time.time()
    # time.clock()
    elapsed = 0
    if enable_print: print(f'Setting timer for {seconds} seconds')
    while elapsed < seconds:
        elapsed = time.time() - start
        time.sleep(0.2)

    packet = {'time': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
              'command': 'stopwatch_alarm',
              'state': 'done',
              'page': page
              }
    rabbitMQ.publish(exchange='main', routing_key='stopwatch', body=packet)
    if enable_print: print(" [x] Sent %r:%r" % ('stopwatch', packet))
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int)
    parser.add_argument('--page', type=int, default=0)

    args = parser.parse_args()

    rabbitMQ = RbmqHandler('stopwatch')
    rabbitMQ.declare_exchanges(['main'])

    stopwatch(args)
