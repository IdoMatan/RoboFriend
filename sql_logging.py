import psycopg2
import time
from datetime import datetime, timezone


class DatabaseLogger:
    def __init__(self, user, password, host, port, database):
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.cursor = None
        self.connection = False

    def connect(self):
        try:
            self.connection = psycopg2.connect(user=self.user,
                                               password=self.password,
                                               host=self.host,
                                               port=self.port,
                                               sslmode='disable',
                                               database=self.database)

            self.cursor = self.connection.cursor()
            print (self.connection.get_dsn_parameters(), "\n")

            # Print PostgreSQL version
            self.cursor.execute("SELECT version();")
            record = self.cursor.fetchone()
            print("You are connected to - ", record,"\n")

            return True

        except (Exception, psycopg2.Error) as error:
            print ("Error while connecting to PostgreSQL", error)
            return False

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection is closed")
        else:
            print('No Postgres connection available to close...')

    # def log(self, mic=None, n_kids=None, attention=None, page_num=None, story=None):
    #
    #     # time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    #     utc_dt = datetime.now(timezone.utc)  # UTC time
    #     time_stamp = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
    #
    #     # print(utc_dt, time_String_temp)
    #
    #     if mic:
    #         insert = ''' INSERT INTO bear_metrics
    #                                 (ts, mic, page_num)
    #                           VALUES
    #                                 (%s, %s, %s);'''
    #
    #         self.cursor.execute(insert, (time_stamp, mic, page_num))
    #         self.connection.commit()
    #
    #     elif n_kids and attention:
    #         insert = ''' INSERT INTO bear_metrics
    #                                 (ts, n_kids, attention_avg)
    #                           VALUES
    #                                 (%s, %s, %s);'''
    #
    #         self.cursor.execute(insert, (time_stamp, n_kids, attention))
    #         self.connection.commit()
    #
    #     elif page_num and story:
    #         insert = ''' INSERT INTO bear_metrics
    #                                 (ts, page_num, story)
    #                           VALUES
    #                                 (%s, %s, %s);'''
    #
    #         self.cursor.execute(insert, (time_stamp, page_num, story))
    #         self.connection.commit()
    #
    #     else:
    #         print('enter either a mic record or n_kids')

    # def log_metric(self, message, story, session):
    #     insert = ''' INSERT INTO bear_metrics
    #                                         (ts, story, session_id, mic_volume, mic_diff,n_kids,attention_avg,excitement,page_num)
    #                                   VALUES
    #                                         (%s, %s, %s, %s, %s, %s, %s, %s, %s);'''
    #
    #     self.cursor.execute(insert, (message.get('time'), story, session, message.get('volume'), message.get('sound_diff'),
    #                                  message['n_kids'], message['attention'], message['excitation'], message['page']))
    #     self.connection.commit()

    def log(self, message, page, session, story):
        insert = ''' INSERT INTO bear_metrics
                                            (ts, story, page, session_id, mic_volume, mic_diff,n_kids,attention_avg,excitement, prev_action1, prev_action2, prev_action3)
                                      VALUES
                                            (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''

       #  insert = "INSERT INTO bear_metrics (ts, story,page_num, session_id, mic_volume, mic_diff,n_kids,attention_avg,excitement, prev_action1, prev_action2, prev_action3) VALUES " \
       #           "({ts}, {story}, {page_num},{session_id}, {mic_volume}, {mic_diff},{n_kids},{attention_avg}, {excitement}, {prev_action1}, {prev_action2},{prev_action3})"
       #
       #  self.cursor.execute(insert.format(ts=message.get('time'),
       #                                    story=story, page=page,
       #                                    session_id=session,
       #                                    mic_volume=message.get('volume'),
       #                                    mic_diff=message.get('sound_diff'),
       #                                    n_kids=message.get('n_kids'),
       #                                    attention_avg=message.get('attention'),
       #                                    excitement=message.get('excitation'),
       #                                    page_num=message.get('page'),
       #                                    prev_action1=message.get('action_prev1'),
       #                                    prev_action2=message.get('action_prev2'),
       #                                    prev_action3=message.get('action_prev3')))
       #
       # # self.cursor.execute (insert)
        self.cursor.execute(insert, (message.get('time'), story, page, session, message.get('volume'), message.get('sound_diff'),
                                     message.get('n_kids'), message.get('attention'), message.get('excitation'),
                                     message.get('action_prev1') if not None else 'null',
                                     message.get('action_prev2') if not None else 'null',
                                     message.get('action_prev3') if not None else 'null'))
        self.connection.commit()
        '''
            ts timestamp with time zone NOT NULL,
            story text,
            session_id real,
            mic_volume real,
            mic_diff real,
            n_kids integer,
            attention_avg real,
            excitement real,
            page_num integer
            prev_action1 integer,
            prev_action2 integer,
            prev_action3 integer
            );
        '''

    def get_state(page):
        pass
        # query = '''SELECT ts, page_num'''

    def clear_db(self):
        delete = ''' DELETE FROM bear_metrics'''
        self.cursor.execute(delete)
        self.connection.commit()
        print('Cleared entire table')
