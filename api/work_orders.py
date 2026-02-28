# -*- coding: utf-8 -*-
"""生产工单管理"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row, is_unique_violation
from api.auth import require_admin

work_orders_bp = Blueprint('work_orders', __name__)

@work_orders_bp.route('', methods=['GET'])
@jwt_required()
def list_orders():
    status = request.args.get('status', '').strip()
    with get_db() as conn:
        c = conn.cursor()
        if status:
            c.execute(
                "SELECT * FROM work_orders WHERE status = ? ORDER BY delivery_date DESC, id DESC",
                (status,)
            )
        else:
            c.execute("SELECT * FROM work_orders ORDER BY delivery_date DESC, id DESC")
        rows = c.fetchall()
    return jsonify({'ok': True, 'data': [dict_from_row(r) for r in rows]})

@work_orders_bp.route('', methods=['POST'])
@require_admin
def create_order():
    data = request.get_json() or {}
    order_no = (data.get('order_no') or '').strip()
    style_code = (data.get('style_code') or '').strip()
    style_name = (data.get('style_name') or '').strip() or None
    quantity = int(data.get('quantity', 0) or 0)
    delivery_date = (data.get('delivery_date') or '').strip() or None
    if not order_no or not style_code:
        return jsonify({'ok': False, 'msg': '工单号和款式编码不能为空'}), 400
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                """INSERT INTO work_orders (order_no, style_code, style_name, quantity, delivery_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_no, style_code, style_name, quantity, delivery_date)
            )
            rid = c.lastrowid
        except Exception as e:
            if is_unique_violation(e):
                return jsonify({'ok': False, 'msg': '工单号已存在'}), 400
            raise
    return jsonify({'ok': True, 'id': rid})

@work_orders_bp.route('/<int:oid>', methods=['PUT'])
@require_admin
def update_order(oid):
    data = request.get_json() or {}
    style_name = (data.get('style_name') or '').strip() or None
    quantity = data.get('quantity')
    delivery_date = (data.get('delivery_date') or '').strip() or None
    status = (data.get('status') or '').strip() or None
    with get_db() as conn:
        c = conn.cursor()
        updates = []
        params = []
        if style_name is not None:
            updates.append('style_name=?')
            params.append(style_name)
        if quantity is not None:
            updates.append('quantity=?')
            params.append(quantity)
        if delivery_date is not None:
            updates.append('delivery_date=?')
            params.append(delivery_date)
        if status:
            updates.append('status=?')
            params.append(status)
        if not updates:
            return jsonify({'ok': True})
        params.append(oid)
        c.execute(f"UPDATE work_orders SET {', '.join(updates)} WHERE id=?", params)
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '工单不存在'}), 404
    return jsonify({'ok': True})

@work_orders_bp.route('/<int:oid>', methods=['DELETE'])
@require_admin
def delete_order(oid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM work_orders WHERE id = ?", (oid,))
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '工单不存在'}), 404
    return jsonify({'ok': True})
