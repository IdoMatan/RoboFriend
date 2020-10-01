import pika
import atexit
import json


class RbmqHandler:
    '''
    A simple RabbitMQ handler class, the broker should either run locally or on remote server and the host
    address set appropriately
    '''
    def __init__(self, service_id, user='rabbitmq', password='rabbitmq', host='13.58.106.247'):
        self.user = user
        self.id = service_id
        self.password = password
        self.host = host
        self.channel, self.connection = self.setup()
        self.queues = []
        self.exchanges = set()
        atexit.register(self.close)

    def setup(self):
        '''
        Setup the connection and channels (run once per service)
        '''
        credentials = pika.PlainCredentials(self.user, self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, credentials=credentials))
        channel = connection.channel()
        return channel, connection

    def declare_exchanges(self, names, exchange_type='topic'):
        '''
        create exchanges - technically could only be done in one of the services
        but no harm in declaring it again (it knows to ignore if already declared)
        :param names: names of the exhanges to create (e.g., 'main'...)
        '''
        for name in names:
            self.channel.exchange_declare(exchange=name, exchange_type=exchange_type)
            self.exchanges.add(name)

    def setup_queues(self):
        '''
        run to setup initial queues if any
        '''
        for queue in self.queues:
            queue_name = self.get_queue_name(queue['name'])
            result = self.channel.queue_declare(queue=queue_name, exclusive=True)
            if queue['exchange'] in self.exchanges:
                self.channel.queue_bind(exchange=queue['exchange'], queue=queue_name, routing_key=queue['key'])
                if queue['callback'] != 'get':
                    self.channel.basic_consume(queue=queue_name, on_message_callback=queue['callback'], auto_ack=True)
            else:
                print('non-existing exchange')

    def add_queue(self, queues):
        '''
        If wanted to add additional queues after setup
        :param queues: list of queues we want to setup, each queue is a dictionary:
                        (name, exchange, key, callback) for example ('video, 'Main', 'actions', callback_function)
        '''
        for queue in queues:
            queue_name = self.get_queue_name(queue['name'])
            result = self.channel.queue_declare(queue=queue_name, exclusive=True)
            self.queues.append(queue)
            if queue['exchange'] in self.exchanges:
                self.channel.queue_bind(exchange=queue['exchange'], queue=queue_name, routing_key=queue['key'])
                if queue['callback'] != 'get':
                    self.channel.basic_consume(queue=queue_name, on_message_callback=queue['callback'], auto_ack=True)
            else:
                print('non-existing exchange')

    def start_consume(self):
        '''
        Start consuming on queues
        '''
        print('\nStarting listening to queues:')
        [print(queue, sep='\n') for queue in self.queues]
        self.channel.start_consuming()

    def pull_from_queue(self, queue_name):
        '''
        :param queue_name: name of queue to pull message from
        :return: tuple (method, properties, body) or (None, None,None) if empty
        '''
        return self.channel.basic_get(queue=self.get_queue_name(queue_name), auto_ack=True)

    def get_queue_name(self, queue):
        '''
        :param queue: name of queue
        :return: id specific queue name
        '''
        return self.id + '-' + queue

    def publish(self, exchange, routing_key, body, add_id=True):
        '''
        basic publish to exchange with added app_id property
        :param exchange: name of exchange to send message to
        :param routing_key: queue routing key
        :param body: payload of message
        :param add_id: boolean flag if want to add app_id to message
        :return: 0 if failed to send, 1 if all ok
        '''

        assert(exchange not in self.exchanges, 'Publish failed - Sending to a non-declared exchange')

        new_properties = pika.BasicProperties(app_id=self.id if add_id else None)
        self.channel.basic_publish(exchange=exchange,
                                   properties=new_properties,
                                   routing_key=routing_key,
                                   body=json.dumps(body) if type(body) is dict else body)
        return 1

    def close(self):
        ''' Close connection gracefully '''
        self.connection.close()
