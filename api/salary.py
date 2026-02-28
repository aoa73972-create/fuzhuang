# -*- coding: utf-8 -*-
"""薪资核算 - 自动计算、日/月汇总、工资条"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row, date_month_sql
from api.auth import require_admin, get_current_employee_id

salary_bp = Blueprint('salary', __name__)

@salary_bp.route('/summary', methods=['GET'])
@jwt_required()
def salary_summary():
    """按日/月汇总薪资"""
    emp_id = get_current_employee_id()
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', '').strip()
    if emp_id and employee_id and employee_id != emp_id:
        return jsonify({'ok': False, 'msg': '无权限查看他人数据'}), 403
    if emp_id:
        employee_id = emp_id
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT pr.record_date, pr.employee_id, e.name as employee_name, e.employee_no,
                   SUM(pr.quantity) as total_qty, SUM(pr.amount) as total_amount
            FROM piece_records pr
            JOIN employees e ON pr.employee_id = e.id
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND pr.employee_id = ?"
            params.append(employee_id)
        if month:
            sql += f" AND {date_month_sql('pr.record_date')} = ?"
            params.append(month)
        sql += " GROUP BY pr.record_date, pr.employee_id ORDER BY pr.record_date DESC, pr.employee_id"
        c.execute(sql, params)
        daily = [dict_from_row(r) for r in c.fetchall()]
        # 月度汇总
        dm = date_month_sql('pr.record_date')
        sql2 = f"""
            SELECT pr.employee_id, e.name as employee_name, e.employee_no,
                   {dm} as month,
                   SUM(pr.quantity) as total_qty, SUM(pr.amount) as total_amount
            FROM piece_records pr
            JOIN employees e ON pr.employee_id = e.id
            WHERE 1=1
        """
        params2 = []
        if employee_id:
            sql2 += " AND pr.employee_id = ?"
            params2.append(employee_id)
        if month:
            sql2 += f" AND {dm} = ?"
            params2.append(month)
        sql2 += f" GROUP BY pr.employee_id, {dm} ORDER BY month DESC, pr.employee_id"
        c.execute(sql2, params2)
        monthly = [dict_from_row(r) for r in c.fetchall()]
    return jsonify({'ok': True, 'daily': daily, 'monthly': monthly})

@salary_bp.route('/slip', methods=['GET'])
@jwt_required()
def salary_slip():
    """生成工资条 - 按员工+月份"""
    emp_id = get_current_employee_id()
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', '').strip()
    if not month:
        return jsonify({'ok': False, 'msg': '请指定月份'}), 400
    if emp_id and employee_id and employee_id != emp_id:
        return jsonify({'ok': False, 'msg': '无权限查看他人数据'}), 403
    if emp_id:
        employee_id = emp_id
    with get_db() as conn:
        c = conn.cursor()
        sql = f"""
            SELECT pr.*, e.name as employee_name, e.employee_no,
                   wo.order_no, wo.style_name
            FROM piece_records pr
            JOIN employees e ON pr.employee_id = e.id
            LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
            WHERE {date_month_sql('pr.record_date')} = ?
        """
        params = [month]
        if employee_id:
            sql += " AND pr.employee_id = ?"
            params.append(employee_id)
        sql += " ORDER BY pr.record_date, pr.style_code, pr.process_name"
        c.execute(sql, params)
        rows = c.fetchall()
    records = [dict_from_row(r) for r in rows]
    # 汇总
    total_amount = sum(r['amount'] or 0 for r in records)
    total_qty = sum(r['quantity'] or 0 for r in records)
    employees = {}
    for r in records:
        eid = r['employee_id']
        if eid not in employees:
            employees[eid] = {'employee_name': r['employee_name'], 'employee_no': r['employee_no'], 'items': [], 'total': 0}
        employees[eid]['items'].append(r)
        employees[eid]['total'] += r['amount'] or 0
    return jsonify({
        'ok': True,
        'month': month,
        'records': records,
        'summary': {'total_amount': total_amount, 'total_qty': total_qty},
        'by_employee': list(employees.values())
    })
