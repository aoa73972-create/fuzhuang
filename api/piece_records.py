# -*- coding: utf-8 -*-
"""计件数据录入 - 支持按日/按工单、批量、扫码"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row, date_month_sql
from api.auth import require_admin, get_current_employee_id

piece_records_bp = Blueprint('piece_records', __name__)

def _get_unit_price(conn, style_code, process_name=None, size=None):
    c = conn.cursor()
    size = (size or '').strip() or None
    process_name = (process_name or '').strip() or None
    # 优先匹配 款式+工序+尺码
    c.execute(
        "SELECT unit_price FROM piece_rates WHERE style_code=? AND (process_name=? OR (process_name IS NULL AND ? IS NULL)) AND (size=? OR (size IS NULL AND ? IS NULL)) LIMIT 1",
        (style_code, process_name, process_name, size, size)
    )
    row = c.fetchone()
    if row:
        return row['unit_price']
    # 再匹配 款式+尺码
    c.execute("SELECT unit_price FROM piece_rates WHERE style_code=? AND (size=? OR (size IS NULL AND ? IS NULL)) LIMIT 1", (style_code, size, size))
    row = c.fetchone()
    if row:
        return row['unit_price']
    # 最后匹配款式
    c.execute("SELECT unit_price FROM piece_rates WHERE style_code=? LIMIT 1", (style_code,))
    row = c.fetchone()
    return row['unit_price'] if row else 0

@piece_records_bp.route('', methods=['GET'])
@jwt_required()
def list_records():
    """计件记录列表 - 支持按员工、月份、工单筛选"""
    emp_id = get_current_employee_id()
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', '').strip()  # YYYY-MM
    record_date = request.args.get('record_date', '').strip()  # YYYY-MM-DD 按日
    start_date = request.args.get('start_date', '').strip()  # 日期范围起
    end_date = request.args.get('end_date', '').strip()  # 日期范围止
    size = request.args.get('size', '').strip()
    work_order_id = request.args.get('work_order_id', type=int)
    if emp_id and employee_id and employee_id != emp_id:
        return jsonify({'ok': False, 'msg': '无权限查看他人数据'}), 403
    if emp_id:
        employee_id = emp_id
    with get_db() as conn:
        c = conn.cursor()
        sql = """
            SELECT pr.*, e.name as employee_name, e.employee_no,
                   wo.order_no, wo.style_name as order_style_name,
                   pr.size
            FROM piece_records pr
            LEFT JOIN employees e ON pr.employee_id = e.id
            LEFT JOIN work_orders wo ON pr.work_order_id = wo.id
            WHERE 1=1
        """
        params = []
        if employee_id:
            sql += " AND pr.employee_id = ?"
            params.append(employee_id)
        if month:
            sql += f" AND {date_month_sql('pr.record_date')} = ?"
            params.append(month)
        if size:
            sql += " AND pr.size = ?"
            params.append(size)
        if work_order_id:
            sql += " AND pr.work_order_id = ?"
            params.append(work_order_id)
        if record_date:
            sql += " AND pr.record_date = ?"
            params.append(record_date)
        if start_date:
            sql += " AND pr.record_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND pr.record_date <= ?"
            params.append(end_date)
        sql += " ORDER BY pr.record_date DESC, pr.id DESC"
        c.execute(sql, params)
        rows = c.fetchall()
    return jsonify({'ok': True, 'data': [dict_from_row(r) for r in rows]})

@piece_records_bp.route('', methods=['POST'])
@require_admin
def create_record():
    """单条录入"""
    data = request.get_json() or {}
    ok, err = _save_record(data)
    if ok:
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'msg': err}), 400

@piece_records_bp.route('/by-style', methods=['POST'])
@require_admin
def create_by_style():
    """按款式+尺码批量录入：先选款式尺码单价，再按人名录入数量"""
    data = request.get_json() or {}
    style_code = (data.get('style_code') or '').strip()
    size = (data.get('size') or '').strip() or None
    unit_price = data.get('unit_price')
    if unit_price is not None:
        unit_price = float(unit_price)
    record_date = (data.get('record_date') or '').strip()
    items = data.get('items', [])  # [{ employee_id, quantity }]
    if not style_code:
        return jsonify({'ok': False, 'msg': '款式不能为空'}), 400
    if not record_date:
        return jsonify({'ok': False, 'msg': '日期不能为空'}), 400
    if unit_price is None or unit_price < 0:
        return jsonify({'ok': False, 'msg': '请填写单价'}), 400
    if not items:
        return jsonify({'ok': False, 'msg': '请录入至少一条数量'}), 400
    saved = 0
    errors = []
    for i, item in enumerate(items):
        emp_id = int(item.get('employee_id', 0) or 0)
        qty = int(item.get('quantity', 0) or 0)
        if qty <= 0:
            continue
        if not emp_id:
            errors.append({'index': i, 'msg': '员工不能为空'})
            continue
        ok, err = _save_record({
            'employee_id': emp_id,
            'style_code': style_code,
            'process_name': None,
            'size': size,
            'record_date': record_date,
            'quantity': qty,
            'unit_price': unit_price
        })
        if ok:
            saved += 1
        else:
            errors.append({'index': i, 'msg': err})
    return jsonify({'ok': True, 'saved': saved, 'errors': errors})

@piece_records_bp.route('/batch', methods=['POST'])
@require_admin
def batch_create():
    """批量录入"""
    data = request.get_json() or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'ok': False, 'msg': '请提供录入数据'}), 400
    saved = 0
    errors = []
    for i, item in enumerate(items):
        res = _save_record(item)
        if res[0]:
            saved += 1
        else:
            errors.append({'index': i, 'msg': res[1]})
    return jsonify({'ok': True, 'saved': saved, 'errors': errors})

@piece_records_bp.route('/scan', methods=['POST'])
@require_admin
def scan_entry():
    """扫码录入 - 格式: 员工ID|款式|工序|数量 或 工单号|员工ID|款式|工序|数量"""
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    record_date = (data.get('record_date') or '').strip()
    if not code:
        return jsonify({'ok': False, 'msg': '扫码内容不能为空'}), 400
    if not record_date:
        from datetime import date
        record_date = str(date.today())
    parts = [p.strip() for p in code.split('|') if p.strip()]
    if len(parts) == 4:
        employee_id, style_code, process_name, qty = int(parts[0]), parts[1], parts[2], int(parts[3])
        work_order_id = None
    elif len(parts) == 5:
        order_no, employee_id, style_code, process_name, qty = parts[0], int(parts[1]), parts[2], parts[3], int(parts[4])
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM work_orders WHERE order_no = ?", (order_no,))
            row = c.fetchone()
            work_order_id = row['id'] if row else None
    else:
        return jsonify({'ok': False, 'msg': '扫码格式错误，应为: 员工ID|款式|工序|数量 或 工单号|员工ID|款式|工序|数量'}), 400
    return _save_record({
        'employee_id': employee_id,
        'work_order_id': work_order_id,
        'style_code': style_code,
        'process_name': process_name or None,
        'record_date': record_date,
        'quantity': qty
    }, source='scan')

def _save_record(data, source='manual'):
    """保存单条计件记录，校验负数、必填项。返回 (ok, error_msg)"""
    employee_id = int(data.get('employee_id', 0) or 0)
    work_order_id = data.get('work_order_id')
    if work_order_id is not None:
        work_order_id = int(work_order_id) or None
    style_code = (data.get('style_code') or '').strip()
    process_name = (data.get('process_name') or '').strip() or None
    size = (data.get('size') or '').strip() or None
    record_date = (data.get('record_date') or '').strip()
    quantity = int(data.get('quantity', 0) or 0)
    override_unit_price = data.get('unit_price')  # 若传入则直接使用，不查库
    if not employee_id:
        return (False, '请选择员工')
    if not style_code:
        return (False, '款式编码不能为空')
    if not record_date:
        return (False, '录入日期不能为空')
    if quantity < 0:
        return (False, '数量不能为负数')
    if quantity == 0:
        return (False, '数量不能为0')
    with get_db() as conn:
        unit_price = override_unit_price if override_unit_price is not None else _get_unit_price(conn, style_code, process_name, size)
        amount = round(quantity * float(unit_price), 2)
        c = conn.cursor()
        c.execute(
            """INSERT INTO piece_records (employee_id, work_order_id, style_code, process_name, size, record_date, quantity, unit_price, amount, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (employee_id, work_order_id, style_code, process_name, size, record_date, quantity, unit_price, amount, source)
        )
    return (True, None)

@piece_records_bp.route('/clear-all', methods=['POST'])
@require_admin
def clear_all():
    """清除所有计件记录"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM piece_records")
        count = c.rowcount
    return jsonify({'ok': True, 'deleted': count})

@piece_records_bp.route('/<int:rid>', methods=['PUT'])
@require_admin
def update_record(rid):
    data = request.get_json() or {}
    size = data.get('size')
    if size is not None:
        size = (str(size).strip() or None) if str(size).strip() else None
    quantity = data.get('quantity')
    if quantity is not None:
        quantity = int(quantity)
        if quantity < 0:
            return jsonify({'ok': False, 'msg': '数量不能为负数'}), 400
    unit_price = data.get('unit_price')
    if unit_price is not None:
        unit_price = float(unit_price)
        if unit_price < 0:
            return jsonify({'ok': False, 'msg': '单价不能为负数'}), 400
    if size is None and quantity is None and unit_price is None:
        return jsonify({'ok': True})
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM piece_records WHERE id = ?", (rid,))
        row = c.fetchone()
        if not row:
            return jsonify({'ok': False, 'msg': '记录不存在'}), 404
        updates = []
        params = []
        new_size = size if size is not None else (row['size'] or None)
        new_qty = quantity if quantity is not None else row['quantity']
        new_price = unit_price if unit_price is not None else (row['unit_price'] or _get_unit_price(conn, row['style_code'], row['process_name'], new_size))
        new_amount = round(new_qty * float(new_price), 2)
        if size is not None:
            updates.append("size=?")
            params.append(new_size)
        if quantity is not None:
            updates.append("quantity=?")
            params.append(new_qty)
        if unit_price is not None or size is not None:
            updates.append("unit_price=?")
            params.append(new_price)
        updates.append("amount=?")
        params.append(new_amount)
        params.append(rid)
        c.execute("UPDATE piece_records SET " + ", ".join(updates) + " WHERE id=?", params)
    return jsonify({'ok': True})

@piece_records_bp.route('/<int:rid>', methods=['DELETE'])
@require_admin
def delete_record(rid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM piece_records WHERE id = ?", (rid,))
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '记录不存在'}), 404
    return jsonify({'ok': True})
