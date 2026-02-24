# -*- coding: utf-8 -*-
"""可视化统计 - 工序薪资占比、员工产能排行"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row
from api.auth import get_current_employee_id

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/process-share', methods=['GET'])
@jwt_required()
def process_share():
    """各工序薪资占比"""
    emp_id = get_current_employee_id()
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', '').strip()
    if emp_id and employee_id and employee_id != emp_id:
        return jsonify({'ok': False, 'msg': '无权限'}), 403
    if emp_id:
        employee_id = emp_id
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT COALESCE(pr.process_name, pr.style_code) as label, SUM(pr.quantity) as qty, SUM(pr.amount) as value
            FROM piece_records pr
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND pr.employee_id = ?"
            params.append(employee_id)
        if month:
            sql += " AND strftime('%Y-%m', pr.record_date) = ?"
            params.append(month)
        sql += " GROUP BY COALESCE(pr.process_name, pr.style_code) ORDER BY value DESC"
        c.execute(sql, params)
        rows = c.fetchall()
    total = sum(r['value'] or 0 for r in rows)
    data = [{'label': r['label'] or '未分类', 'qty': r['qty'] or 0, 'value': round(r['value'] or 0, 2), 'percent': round((r['value'] or 0) / total * 100, 1) if total else 0} for r in rows]
    return jsonify({'ok': True, 'data': data, 'total': round(total, 2)})

@stats_bp.route('/employee-ranking', methods=['GET'])
@jwt_required()
def employee_ranking():
    """员工产能排行"""
    emp_id = get_current_employee_id()
    month = request.args.get('month', '').strip()
    limit = request.args.get('limit', type=int) or 20
    if emp_id:
        # 普通员工只看自己
        with get_db() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT e.id, e.name, e.employee_no, SUM(pr.quantity) as total_qty, SUM(pr.amount) as total_amount
                FROM employees e
                JOIN piece_records pr ON pr.employee_id = e.id
                WHERE e.id = ? AND (? = '' OR strftime('%Y-%m', pr.record_date) = ?)
                GROUP BY e.id
            """, (emp_id, month, month))
            row = c.fetchone()
        if row:
            return jsonify({'ok': True, 'data': [dict_from_row(row)], 'total': 1})
        return jsonify({'ok': True, 'data': [], 'total': 0})
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT e.id, e.name, e.employee_no, SUM(pr.quantity) as total_qty, SUM(pr.amount) as total_amount
            FROM employees e
            JOIN piece_records pr ON pr.employee_id = e.id
            WHERE 1=1
        """
        params = []
        if month:
            sql += " AND strftime('%Y-%m', pr.record_date) = ?"
            params.append(month)
        sql += " GROUP BY e.id ORDER BY total_amount DESC LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        rows = c.fetchall()
    data = []
    for i, r in enumerate(rows, 1):
        d = dict_from_row(r)
        d['rank'] = i
        data.append(d)
    return jsonify({'ok': True, 'data': data})
