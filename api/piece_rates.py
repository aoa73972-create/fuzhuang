# -*- coding: utf-8 -*-
"""计件单价管理"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import get_db, dict_from_row, is_unique_violation
from api.auth import require_admin

piece_rates_bp = Blueprint('piece_rates', __name__)

@piece_rates_bp.route('', methods=['GET'])
@jwt_required()
def list_rates():
    style_code = request.args.get('style_code', '').strip()
    with get_db() as conn:
        c = conn.cursor()
        if style_code:
            c.execute(
                "SELECT * FROM piece_rates WHERE style_code = ? ORDER BY process_name",
                (style_code,)
            )
        else:
            c.execute("SELECT * FROM piece_rates ORDER BY style_code, process_name")
        rows = c.fetchall()
    return jsonify({'ok': True, 'data': [dict_from_row(r) for r in rows]})

@piece_rates_bp.route('', methods=['POST'])
@require_admin
def create_rate():
    data = request.get_json() or {}
    style_code = (data.get('style_code') or '').strip()
    style_name = (data.get('style_name') or '').strip() or None
    process_name = (data.get('process_name') or '').strip() or None
    size = (data.get('size') or '').strip() or ''  # 空字符串避免 UNIQUE 中 NULL 问题
    unit_price = float(data.get('unit_price', 0))
    if not style_code:
        return jsonify({'ok': False, 'msg': '款式编码不能为空'}), 400
    if unit_price < 0:
        return jsonify({'ok': False, 'msg': '单价不能为负数'}), 400
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO piece_rates (style_code, style_name, process_name, size, unit_price) VALUES (?, ?, ?, ?, ?)",
                (style_code, style_name, process_name, size or '', unit_price)
            )
            rid = c.lastrowid
        except Exception as e:
            if is_unique_violation(e):
                return jsonify({'ok': False, 'msg': '该款式工序单价已存在'}), 400
            raise
    return jsonify({'ok': True, 'id': rid})

@piece_rates_bp.route('/<int:rid>', methods=['PUT'])
@require_admin
def update_rate(rid):
    data = request.get_json() or {}
    unit_price = float(data.get('unit_price', 0))
    if unit_price < 0:
        return jsonify({'ok': False, 'msg': '单价不能为负数'}), 400
    style_name = (data.get('style_name') or '').strip() or None
    size = (data.get('size') or '').strip() or ''
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE piece_rates SET unit_price=?, style_name=?, size=? WHERE id=?",
            (unit_price, style_name, size, rid)
        )
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '记录不存在'}), 404
    return jsonify({'ok': True})

@piece_rates_bp.route('/<int:rid>', methods=['DELETE'])
@require_admin
def delete_rate(rid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM piece_rates WHERE id = ?", (rid,))
        if c.rowcount == 0:
            return jsonify({'ok': False, 'msg': '记录不存在'}), 404
    return jsonify({'ok': True})
