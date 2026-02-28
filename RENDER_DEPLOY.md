# Render 一键部署指南

## 前置条件

1. 代码已推送到 **GitHub**
2. 已有 [Render](https://render.com) 账号（可用 GitHub 登录）

---

## 部署步骤

### 1. 推送代码到 GitHub

```bash
cd /Users/mima0000/时代新区计件系统
git init
git add .
git commit -m "计件系统"
git branch -M main
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

> 若已有 GitHub 仓库，直接 `git push` 即可。

### 2. 在 Render 一键部署

1. 打开 https://dashboard.render.com
2. 点击 **New** → **Blueprint**
3. 连接 GitHub，选择你的仓库
4. Render 会自动识别根目录的 `render.yaml`，创建：
   - **piecework-db**：免费 PostgreSQL 数据库
   - **piecework-api**：Flask 应用（前后端一体）
5. 点击 **Apply**，等待部署完成（约 3–5 分钟）

### 3. 获取访问地址

1. 在 **piecework-api** 服务详情页，复制 **URL**
2. 形如：`https://piecework-api-xxxx.onrender.com`
3. 直接访问该 URL 即可使用系统

---

## 登录账号

部署完成后，首次访问时自动创建以下管理员账号：

| 账户       | 密码    |
|------------|---------|
| 13396010619 | 919298 |
| admin      | admin123 |

---

## 注意事项

1. **免费版休眠**：约 15 分钟无访问会休眠，下次访问需等待约 30 秒唤醒
2. **PostgreSQL 免费版**：Render 免费数据库有 30 天有效期，到期后需升级或重新创建
3. **数据持久化**：使用 PostgreSQL，数据不会因服务重启丢失
