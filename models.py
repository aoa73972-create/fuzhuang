# -*- coding: utf-8 -*-
"""数据模型 - 员工、工单、计件单价、计件记录"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os

import config

def get_db_path():
    db_dir = os.path.join(config.BASE_DIR, 'data')
    os.makedirs(db_dir, exist_ok=True)
    return config.DATABASE

@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    """初始化数据库表"""
    with get_db() as conn:
        c = conn.cursor()
        # 用户表（含权限）
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
        # 员工表
        c.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_no TEXT UNIQUE,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 款式/工序/尺码计件单价表
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
        # 生产工单表
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
        # 计件记录表
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
        # 创建索引
        c.execute('CREATE INDEX IF NOT EXISTS idx_piece_employee_date ON piece_records(employee_id, record_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_piece_record_date ON piece_records(record_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_piece_work_order ON piece_records(work_order_id)')
        # 迁移：添加 size 列（若不存在）
        for tbl, col in [('piece_rates', 'size'), ('piece_records', 'size')]:
            try:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # 列已存在

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)
