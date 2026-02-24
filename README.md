# 时代新区服装加工厂 - 员工薪资计件系统

贴合服装加工厂场景的计件薪资管理系统，满足「款式计件 + 数据可追溯 + 操作简单」。

## 功能模块

- **基础数据管理**：员工信息、计件单价、生产工单
- **计件数据录入**：按款式/尺码批量录入，支持新增员工
- **数据查询**：按日/按月/日期范围查询，支持编辑尺码、数量、单价
- **薪资汇总**：按员工汇总，支持筛选，导出 Excel
- **数据统计**：工序占比、产能排行
- **权限管理**：普通员工仅查看本人数据，管理员可录入/修改/导出

## 技术栈

- **后端**：Python Flask + SQLite
- **前端**：Vue 3 + Element Plus + Vue Router
- **报表**：openpyxl 导出 Excel

## 项目结构

```
├── app.py              # Flask 入口
├── config.py           # 配置
├── models.py           # 数据模型
├── api/                # API 接口
├── static/             # 前端静态资源
├── templates/          # HTML 模板
├── requirements.txt   # Python 依赖
├── render.yaml         # Render 部署配置
└── netlify.toml        # Netlify 部署配置
```

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

## 部署

- **后端**：Render（见 [RENDER_DEPLOY.md](RENDER_DEPLOY.md)）
- **前端**：Netlify（见 [DEPLOY.md](DEPLOY.md)）

## License

MIT
# fuzhuang
