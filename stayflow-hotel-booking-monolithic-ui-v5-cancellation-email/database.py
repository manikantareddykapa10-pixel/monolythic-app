import os
import re
from psycopg import connect
from psycopg.rows import dict_row


class CursorProxy:
    def __init__(self, cursor): self._cursor = cursor
    def fetchone(self): return self._cursor.fetchone()
    def fetchall(self): return self._cursor.fetchall()
    @property
    def rowcount(self): return self._cursor.rowcount

class ConnectionProxy:
    def __init__(self, conn): self._conn = conn
    def execute(self, sql, params=()):
        sql = re.sub(r"\?", "%s", sql)
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return CursorProxy(cur)
    def executemany(self, sql, params):
        sql = re.sub(r"\?", "%s", sql)
        cur = self._conn.cursor(); cur.executemany(sql, params); return CursorProxy(cur)
    def commit(self): self._conn.commit()
    def rollback(self): self._conn.rollback()
    def close(self): self._conn.close()

def get_connection():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required. Copy .env.example to .env and add your Supabase Postgres connection string.")
    return ConnectionProxy(connect(database_url, row_factory=dict_row))

def init_db():
    # Supabase schema is managed by supabase/schema.sql. We only verify connectivity here.
    conn = get_connection()
    try:
        conn.execute("SELECT 1").fetchone()
        # Lightweight forward-compatible migrations for existing Supabase projects.
        conn.execute("ALTER TABLE public.cancellation_requests ADD COLUMN IF NOT EXISTS assigned_manager_id bigint REFERENCES public.users(id) ON DELETE SET NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cancellation_assigned_manager ON public.cancellation_requests(assigned_manager_id, status, created_at DESC)")
        conn.commit()
    finally:
        conn.close()
