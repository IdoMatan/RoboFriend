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

    def log(self, mic=None, n_kids=None, attention=None, page_num=None, story=None):

        # time_stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        utc_dt = datetime.now(timezone.utc)  # UTC time
        time_stamp = utc_dt.strftime('%Y-%m-%d %H:%M:%S')

        # print(utc_dt, time_String_temp)

        if mic:
            insert = ''' INSERT INTO bear_metrics 
                                    (ts, mic, page_num)
                              VALUES
                                    (%s, %s, %s);'''

            self.cursor.execute(insert, (time_stamp, mic, page_num))
            self.connection.commit()

        # if n_kids and not mic:
        #     insert = ''' INSERT INTO bear_metrics
        #                             (time_stamp, n_kids)
        #                       VALUES
        #                             (%s, %s);'''
        #
        #     self.cursor.execute(insert, (time_stamp, n_kids))
        #     self.connection.commit()
        #
        # if n_kids and mic:
        #     insert = ''' INSERT INTO bear_metrics
        #                             (time_stamp, mic, n_kids)
        #                       VALUES
        #                             (%s, %s, %s);'''
        #
        #     self.cursor.execute(insert, (time_stamp, mic, n_kids))
        #     self.connection.commit()

        elif n_kids and attention:
            insert = ''' INSERT INTO bear_metrics 
                                    (ts, n_kids, attention_avg)
                              VALUES
                                    (%s, %s, %s);'''

            self.cursor.execute(insert, (time_stamp, n_kids, attention))
            self.connection.commit()

        elif page_num and story:
            insert = ''' INSERT INTO bear_metrics 
                                    (ts, page_num, story)
                              VALUES
                                    (%s, %s, %s);'''

            self.cursor.execute(insert, (time_stamp, page_num, story))
            self.connection.commit()

        else:
            print('enter either a mic record or n_kids')

    def clear_db(self):
        delete = ''' DELETE FROM bear_metrics'''
        self.cursor.execute(delete)
        self.connection.commit()
        print('Cleared entire table')
