# -*- coding: utf-8 -*-
"""认证与权限"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash

from models import get_db, dict_from_row, init_db, is_unique_violation

auth_bp = Blueprint('auth', __name__)

def _ensure_admin_user():
    """确保存在默认管理员"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = 'admin'")
        if c.fetchone() is None:
            c.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                ('admin', generate_password_hash('admin123'))
            )
        # 确保部署用账号 13396010619 存在
        c.execute("SELECT id FROM users WHERE username = '13396010619'")
        if c.fetchone() is None:
            c.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                ('13396010619', generate_password_hash('919298'))
            )

def _get_user_by_username(username):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        return dict_from_row(c.fetchone())

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'ok': False, 'msg': '请输入用户名和密码'}), 400
    _ensure_admin_user()
    user = _get_user_by_username(username)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'ok': False, 'msg': '用户名或密码错误'}), 401
    token = create_access_token(
        identity=username,
        additional_claims={'role': user['role'], 'user_id': user['id'], 'employee_id': user['employee_id']}
    )
    emp = None
    if user.get('employee_id'):
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, employee_no FROM employees WHERE id = ?", (user['employee_id'],))
            emp = dict_from_row(c.fetchone())
    return jsonify({
        'ok': True,
        'token': token,
        'user': {
            'username': user['username'],
            'role': user['role'],
            'employee_id': user['employee_id'],
            'employee': emp
        }
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    claims = get_jwt()
    username = get_jwt_identity()
    user = _get_user_by_username(username)
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'}), 404
    emp = None
    if user.get('employee_id'):
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, employee_no FROM employees WHERE id = ?", (user['employee_id'],))
            emp = dict_from_row(c.fetchone())
    return jsonify({
        'ok': True,
        'user': {
            'username': user['username'],
            'role': user['role'],
            'employee_id': user['employee_id'],
            'employee': emp
        }
    })

def require_admin(fn):
    """装饰器：仅管理员"""
    from functools import wraps
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'ok': False, 'msg': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    return wrapper

def get_current_employee_id():
    """获取当前登录员工ID（普通员工）"""
    claims = get_jwt()
    return claims.get('employee_id')

@auth_bp.route('/create-user', methods=['POST'])
@require_admin
def create_user():
    """管理员创建员工账号（用于员工登录查看自己的数据）"""
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    employee_id = data.get('employee_id', type=int)
    if not username or not password:
        return jsonify({'ok': False, 'msg': '用户名和密码不能为空'}), 400
    if not employee_id:
        return jsonify({'ok': False, 'msg': '请选择关联员工'}), 400
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password_hash, role, employee_id) VALUES (?, ?, 'employee', ?)",
                (username, generate_password_hash(password), employee_id)
            )
            return jsonify({'ok': True, 'id': c.lastrowid})
        except Exception as e:
            if is_unique_violation(e):
                return jsonify({'ok': False, 'msg': '用户名已存在'}), 400
            raise
