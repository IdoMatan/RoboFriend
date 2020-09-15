import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from sql_logging import *
import json
from rabbitmq.rabbitMQ_utils import *
import logging

database = DatabaseLogger(user="postgres", password=None, host="13.58.106.247", port="5432", database="robo_friend")

database.connect()

formatter = logging.Formatter('%(asctime)s,%(name)s,%(levelname)s,%(message)s')


def setup_local_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


# declare logger
if not os.path.exists('../session_logs/'):
    os.makedirs('../session_logs/')
logger = None


def callback(ch, method, properties, body):
    if properties.app_id == rabbitMQ.id:   # skip messages sent from the same process
        return
    global logger
    message = json.loads(body)
    if properties.app_id == 'app_service' and message['action'] == 'initial_start':
        logger = setup_local_logger('logger',
                                    f'../session_logs/session_{message["session"]}_log_{time.strftime("%a,_%d_%b_%Y_%H_%M_%S")}.txt')

    if logger is not None:
        logger.info(body)

    ### HERE WE NEED TO ADD SQL LOGGING (NEED TO NAIL DOWN COLUMNS NEEDED AND FORMARTTING)

    print(f"Log Callback -> from {properties.app_id}, body: {message}")


rabbitMQ = RbmqHandler('logger')
rabbitMQ.declare_exchanges(['main'])

rabbitMQ.queues.append({'name': 'logger', 'exchange': 'main', 'key': '#', 'callback': callback})
rabbitMQ.setup_queues()
rabbitMQ.start_consume()





# for message in consumer:
#     if message.topic == 'microphone':
#         # print("Logging to database:", message.value['volume'], ', from:', message.key)
#         database.log(mic=float(message.value['volume']))
#
#     elif message.topic == 'camera':
#         # print("Logging to database:", message.value['attention'], ', from:', message.key)
#         database.log(attention=float(message.value['attention']), n_kids=float(message.value['kids']))
#
#     elif message.topic == 'video':
#         # print("Logging to database:", message.value['page'], ', from:', message.key)
#         database.log(page_num=int(message.value['page']), story=message.value['story'])
#
#     elif message.topic == 'logging' and message.value['command'] == 'log_experience':
#         # state: {average attention over page, average noise, n_kids
#         database.log_experience(message.value['experience'])
