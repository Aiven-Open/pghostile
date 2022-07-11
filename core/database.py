# Copyright (c) 2022 Aiven, Helsinki, Finland. https://aiven.io

import psycopg2
import psycopg2.extras
from psycopg2 import Error


class Database:
    def __init__(self, username, password, database, host="127.0.0.1", port=5432, sslmode=None):
        self.conn = psycopg2.connect(
            user=username,
            password=password,
            host=host,
            port=port,
            database=database,
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode=sslmode
        )
        self.conn.autocommit = True
        # self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.cur = self.conn.cursor()

    def query(self, qry, pars=None):
        self.cur.execute(qry, pars)
        self.conn.commit()
        return self.cur

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
