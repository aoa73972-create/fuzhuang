# -*- coding: utf-8 -*-
"""时代新区服装加工厂 - 员工薪资计件系统"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

import config
from models import init_db

# 确保 data 目录存在
os.makedirs(os.path.join(config.BASE_DIR, 'data'), exist_ok=True)
init_db()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400 * 7  # 7天

CORS(app, supports_credentials=True)
JWTManager(app)

# 注册 API 蓝图
from api.auth import auth_bp
from api.employees import employees_bp
from api.piece_rates import piece_rates_bp
from api.work_orders import work_orders_bp
from api.piece_records import piece_records_bp
from api.salary import salary_bp
from api.reports import reports_bp
from api.stats import stats_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(employees_bp, url_prefix='/api/employees')
app.register_blueprint(piece_rates_bp, url_prefix='/api/piece-rates')
app.register_blueprint(work_orders_bp, url_prefix='/api/work-orders')
app.register_blueprint(piece_records_bp, url_prefix='/api/piece-records')
app.register_blueprint(salary_bp, url_prefix='/api/salary')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(stats_bp, url_prefix='/api/stats')

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
