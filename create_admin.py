#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建管理员账号：账户 13396010619，密码 919298"""
import sys
sys.path.insert(0, '.')

from werkzeug.security import generate_password_hash
from models import get_db, init_db

def main():
    init_db()
    username = '13396010619'
    password = '919298'
    password_hash = generate_password_hash(password)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            print(f'用户 {username} 已存在，跳过创建')
            return
        c.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
            (username, password_hash)
        )
        print(f'已创建管理员账号：{username} / {password}')

if __name__ == '__main__':
    main()
