# 计件系统部署指南（Netlify + Render）

本系统为前后端分离架构，需分别部署：
- **前端**：Netlify（静态托管）
- **后端**：Render（Flask API）

---

## 一、部署后端到 Render

1. 登录 [Render](https://render.com)，用 GitHub 登录
2. 点击 **New** → **Web Service**
3. 连接你的 GitHub 仓库（或先推送代码到 GitHub）
4. 配置：
   - **Name**: piecework-api
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt gunicorn`
   - **Start Command**: `gunicorn -w 1 -b 0.0.0.0:$PORT app:app`
   - **Instance Type**: Free
5. 在 **Environment** 中添加：
   - `SECRET_KEY`: 随机字符串（可点 Generate）
   - `JWT_SECRET_KEY`: 随机字符串（可点 Generate）
6. 点击 **Create Web Service**，等待部署完成
7. 记下服务 URL，例如：`https://piecework-api-xxxx.onrender.com`

---

## 二、部署前端到 Netlify

1. 登录 [Netlify](https://netlify.com)
2. 点击 **Add new site** → **Import an existing project**
3. 连接 GitHub 仓库
4. 配置构建：
   - **Build command**: `npm run build:netlify`
   - **Publish directory**: `public`
   - **Base directory**: 留空
5. 点击 **Advanced** → **New variable**，添加环境变量：
   - **Key**: `API_URL`
   - **Value**: 填入 Render 后端 URL（如 `https://piecework-api-xxxx.onrender.com`），**不要**加末尾斜杠
6. 点击 **Deploy site**

---

## 三、配置 CORS（如遇跨域问题）

后端已启用 CORS，若仍有跨域错误，可在 Render 的 **Environment** 中确认 `FLASK_ENV` 等配置。

---

## 四、本地测试构建

```bash
# 设置后端地址并构建
export API_URL=https://your-api.onrender.com
npm run build:netlify

# 本地预览 public 目录
npx serve public
```

---

## 五、注意事项

1. **Render 免费版**：服务 15 分钟无请求会休眠，首次访问需等待约 30 秒唤醒
2. **SQLite 数据**：Render 免费版重启后数据可能丢失，生产环境建议使用 PostgreSQL
3. **默认账号**：首次部署后需在设置中创建管理员账号
