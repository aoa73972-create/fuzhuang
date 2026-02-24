# Render 后端部署步骤

## 前置条件

1. 代码已推送到 **GitHub**（Render 需连接 Git 仓库）
2. 已有 [Render](https://render.com) 账号（可用 GitHub 登录）

---

## 方式一：使用 Blueprint（推荐）

1. 打开 https://dashboard.render.com
2. 点击 **New** → **Blueprint**
3. 连接 GitHub，选择仓库 `时代新区计件系统`
4. Render 会自动识别根目录的 `render.yaml`
5. 点击 **Apply**，等待部署完成
6. 在服务详情页复制 **URL**（如 `https://piecework-api-xxxx.onrender.com`）

---

## 方式二：手动创建 Web Service

1. 打开 https://dashboard.render.com
2. 点击 **New** → **Web Service**
3. 连接 GitHub，选择仓库
4. 填写配置：

   | 配置项 | 值 |
   |--------|-----|
   | Name | piecework-api |
   | Region | Singapore（或离你最近的） |
   | Branch | main |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn -w 1 -b 0.0.0.0:$PORT app:app` |

5. 在 **Environment** 中添加变量（可点 Generate 生成随机值）：
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`

6. 点击 **Create Web Service**
7. 等待构建完成，复制服务 URL

---

## 部署后

- 访问 `https://你的服务名.onrender.com/api/auth/login` 可测试接口
- 默认管理员：`admin` / `admin123`（需在本地或首次部署时初始化）
- 将 URL 填入 Netlify 的 `API_URL` 环境变量

---

## 常见问题

**Q: 首次访问很慢？**  
A: 免费版 15 分钟无请求会休眠，首次访问需约 30 秒唤醒。

**Q: 数据会丢失？**  
A: 免费版重启后 SQLite 数据可能丢失，生产环境建议使用 PostgreSQL。
