# 时代新区服装加工厂 - 员工薪资计件系统

贴合服装加工厂场景的计件薪资管理系统，满足「款式计件 + 数据可追溯 + 操作简单」。

## 功能模块

- **基础数据管理**：员工信息、计件单价、生产工单
- **计件数据录入**：按日/按工单录入，支持批量录入、扫码录入，自动校验
- **薪资核算**：自动计算计件工资，汇总日/月度薪资，生成工资条
- **数据查询与报表**：按员工/月份查询，导出 Excel，可视化统计
- **权限管理**：普通员工仅查看本人数据，管理员可录入/修改/导出

## 技术栈

- 后端：Python Flask + SQLite
- 前端：Vue 3 + Element Plus
- 报表：openpyxl 导出 Excel

## 快速启动

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

访问 http://localhost:5000

**默认管理员**：admin / admin123
