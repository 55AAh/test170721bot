import os
import psycopg2

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

    @property
    def last_update_id(self):
        with self.transaction:
            self.db_cur.execute("SELECT last_update_id FROM info")
            return self.db_cur.fetchone()[0]

    @last_update_id.setter
    def last_update_id(self, value):
        with self.transaction:
            self.db_cur.execute("UPDATE info SET last_update_id = %s", (value,))

    def disconnect(self):
        assert self.db_conn and self.db_cur
        self.db_conn.close()
