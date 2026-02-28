# -*- coding: utf-8 -*-
"""数据库抽象层：支持 SQLite（本地）和 PostgreSQL（Render）"""
import os
from contextlib import contextmanager

# 检测是否使用 PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith(('postgres://', 'postgresql://')))

if IS_POSTGRES:
    # Render 可能返回 postgres://，psycopg2 需要 postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = 'postgresql://' + DATABASE_URL[11:]
    import psycopg2
    from psycopg2 import extras as pg_extras
else:
    import sqlite3
    import config


def _get_sqlite_path():
    db_dir = os.path.join(config.BASE_DIR, 'data')
    os.makedirs(db_dir, exist_ok=True)
    return config.DATABASE


@contextmanager
def get_db():
    """获取数据库连接（上下文管理器）"""
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=pg_extras.RealDictCursor)
        try:
            yield _PGConnection(conn)
            conn.commit()
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(_get_sqlite_path())
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


class _PGCursor:
    """PostgreSQL 游标包装，兼容 SQLite 的 ? 占位符和 lastrowid"""
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn._conn.cursor()
        self._lastrowid = None

    def execute(self, sql, params=None):
        params = params or ()
        # 将 ? 占位符转换为 %s
        if '?' in sql:
            sql = sql.replace('?', '%s')
        self._cursor.execute(sql, params)
        if sql.strip().upper().startswith('INSERT') and 'RETURNING' not in sql.upper():
            try:
                self._cursor.execute('SELECT lastval()')
                self._lastrowid = self._cursor.fetchone()[0]
            except Exception:
                pass
        return self

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._lastrowid

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()


class _PGConnection:
    """PostgreSQL 连接包装，提供 cursor() 接口"""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return _PGCursor(self)


def dict_from_row(row):
    """将行对象转为字典"""
    if row is None:
        return None
    if hasattr(row, 'keys'):
        return dict(row)
    return dict(zip(row.keys(), row))


def is_unique_violation(exc):
    """判断是否为唯一约束冲突（兼容 SQLite 与 PostgreSQL）"""
    s = str(exc).lower()
    return 'unique' in s or 'duplicate' in s


def date_month_sql(column):
    """返回按月份筛选的 SQL 片段（兼容 SQLite 与 PostgreSQL）"""
    if IS_POSTGRES:
        return f"to_char({column}, 'YYYY-MM')"
    return f"strftime('%Y-%m', {column})"


def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        c = conn.cursor()
        if IS_POSTGRES:
            _init_postgres(c)
        else:
            _init_sqlite(c)


def _init_sqlite(c):
    """SQLite 建表"""
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            employee_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_no TEXT UNIQUE,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS piece_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            style_code TEXT NOT NULL,
            style_name TEXT,
            process_name TEXT,
            size TEXT,
            unit_price REAL NOT NULL,
            unit TEXT DEFAULT '件',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(style_code, process_name, size)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            style_code TEXT NOT NULL,
            style_name TEXT,
            quantity INTEGER,
            delivery_date DATE,
            status TEXT DEFAULT '进行中',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (style_code) REFERENCES piece_rates(style_code)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS piece_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            work_order_id INTEGER,
            style_code TEXT NOT NULL,
            process_name TEXT,
            size TEXT,
            record_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL,
            amount REAL,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_piece_employee_date ON piece_records(employee_id, record_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_piece_record_date ON piece_records(record_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_piece_work_order ON piece_records(work_order_id)')
    for tbl, col in [('piece_rates', 'size'), ('piece_records', 'size')]:
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass


def _init_postgres(c):
    """PostgreSQL 建表"""
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            employee_no TEXT UNIQUE,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS piece_rates (
            id SERIAL PRIMARY KEY,
            style_code TEXT NOT NULL,
            style_name TEXT,
            process_name TEXT,
            size TEXT,
            unit_price REAL NOT NULL,
            unit TEXT DEFAULT '件',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(style_code, process_name, size)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id SERIAL PRIMARY KEY,
            order_no TEXT UNIQUE NOT NULL,
            style_code TEXT NOT NULL,
            style_name TEXT,
            quantity INTEGER,
            delivery_date DATE,
            status TEXT DEFAULT '进行中',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS piece_records (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            work_order_id INTEGER REFERENCES work_orders(id),
            style_code TEXT NOT NULL,
            process_name TEXT,
            size TEXT,
            record_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL,
            amount REAL,
            source TEXT DEFAULT 'manual',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            employee_id INTEGER REFERENCES employees(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    for idx, cols in [
        ('idx_piece_employee_date', '(employee_id, record_date)'),
        ('idx_piece_record_date', '(record_date)'),
        ('idx_piece_work_order', '(work_order_id)'),
    ]:
        try:
            c.execute(f'CREATE INDEX IF NOT EXISTS {idx} ON piece_records {cols}')
        except Exception:
            pass
