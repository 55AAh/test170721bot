import psycopg2
import json
import os
import pickle

__all__ = ["Db"]


class _Transaction:
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def __enter__(self):
        pass

    def __exit__(self, *_args):
        self.db_conn.commit()


class Db:
    def __init__(self):
        self.db_conn = None
        self.db_cur = None
        self.transaction = None

    def connect(self, db_url=os.getenv('DATABASE_URL')):
        self.db_conn = psycopg2.connect(db_url)
        self.db_cur = self.db_conn.cursor()
        self.transaction = _Transaction(self.db_conn)
        self.db_cur.execute("SELECT pg_advisory_lock(0)")

    def execute(self, query, *variables):
        with self.transaction:
            self.db_cur.execute(query, vars=variables)

    def fetch_one(self, query, *variables):
        with self.transaction:
            self.db_cur.execute(query, vars=variables)
            return self.db_cur.fetchone()

    def fetch_many(self, query, *variables):
        with self.transaction:
            self.db_cur.execute(query, vars=variables)
            return self.db_cur.fetchmany()

    @property
    def current_promise(self):
        return self.fetch_one("SELECT current_promise FROM info")[0]

    @current_promise.setter
    def current_promise(self, value):
        self.execute("UPDATE info SET current_promise = %s", value)

    @property
    def last_update_id(self):
        return self.fetch_one("SELECT last_update_id FROM info")[0]

    @last_update_id.setter
    def last_update_id(self, value):
        self.execute("UPDATE info SET last_update_id = %s", value)

    def save_update(self, update):
        self.execute("INSERT INTO updates VALUES (now(), %s)", json.dumps(update))

    def disconnect(self):
        assert self.db_conn and self.db_cur
        self.db_conn.close()
