# -*- coding: utf-8 -*-
"""员工管理"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row, is_unique_violation
from api.auth import require_admin, get_current_employee_id

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('', methods=['GET'])
@jwt_required()
def list_employees():
    """员工列表（管理员看全部，员工只看自己）"""
    emp_id = get_current_employee_id()
    with get_db() as conn:
        c = conn.cursor()
        if emp_id:
            c.execute("SELECT id, name, employee_no, department, created_at FROM employees WHERE id = ?", (emp_id,))
        else:
            c.execute("SELECT id, name, employee_no, department, created_at FROM employees ORDER BY id")
        rows = c.fetchall()
    return jsonify({'ok': True, 'data': [dict_from_row(r) for r in rows]})

@employees_bp.route('/batch', methods=['POST'])
@require_admin
def batch_create():
    """批量录入员工姓名 - 每行一个名字，或逗号/空格分隔"""
    data = request.get_json() or {}
    names_text = (data.get('names') or '').strip()
    if not names_text:
        return jsonify({'ok': False, 'msg': '请输入员工姓名'}), 400
    # 支持换行、逗号、空格分隔
    import re
    names = re.split(r'[\n,，\s]+', names_text)
    names = [n.strip() for n in names if n.strip()]
    if not names:
        return jsonify({'ok': False, 'msg': '未解析到有效姓名'}), 400
    added = 0
    skipped = []
    with get_db() as conn:
        c = conn.cursor()
        for name in names:
            c.execute("SELECT id FROM employees WHERE name = ?", (name,))
            if c.fetchone():
                skipped.append(name)
                continue
            c.execute("INSERT INTO employees (name) VALUES (?)", (name,))
            added += 1
    return jsonify({'ok': True, 'added': added, 'skipped': skipped})

@employees_bp.route('', methods=['POST'])
@require_admin
def create_employee():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'ok': False, 'msg': '员工姓名不能为空'}), 400
    employee_no = (data.get('employee_no') or '').strip() or None
    department = (data.get('department') or '').strip() or None
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO employees (name, employee_no, department) VALUES (?, ?, ?)",
                (name, employee_no, department)
            )
            rid = c.lastrowid
        except Exception as e:
            if is_unique_violation(e):
                return jsonify({'ok': False, 'msg': '工号已存在'}), 400
            raise
    return jsonify({'ok': True, 'id': rid})

@employees_bp.route('/<int:eid>', methods=['PUT'])
@require_admin
def update_employee(eid):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'ok': False, 'msg': '员工姓名不能为空'}), 400
    employee_no = (data.get('employee_no') or '').strip() or None
    department = (data.get('department') or '').strip() or None
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE employees SET name=?, employee_no=?, department=? WHERE id=?",
            (name, employee_no, department, eid)
        )
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '员工不存在'}), 404
    return jsonify({'ok': True})

@employees_bp.route('/<int:eid>', methods=['DELETE'])
@require_admin
def delete_employee(eid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM employees WHERE id = ?", (eid,))
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '员工不存在'}), 404
    return jsonify({'ok': True})
