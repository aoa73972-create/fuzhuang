# Render 一键部署指南

## 前置条件

1. 代码已推送到 **GitHub**（仓库：https://github.com/aoa73972-create/fuzhuang）
2. 已有 [Render](https://render.com) 账号（可用 GitHub 登录）

---

## 部署步骤

### 1. 打开 Render 控制台

在浏览器中打开：**https://dashboard.render.com**

### 2. 创建 Blueprint

1. 点击左上角 **New** 按钮
2. 选择 **Blueprint**
3. 若未连接 GitHub，按提示用 GitHub 账号授权 Render
4. 在仓库列表中选择 **aoa73972-create/fuzhuang**（或搜索 `fuzhuang`）
5. 点击 **Connect** 连接仓库

### 3. 应用配置

1. Render 会自动读取仓库根目录的 `render.yaml`
2. 预览将创建的服务：
   - **piecework-db**：免费 PostgreSQL 数据库
   - **piecework-api**：Flask Web 服务
3. 点击 **Apply** 开始部署
4. 等待约 3–5 分钟，直到状态变为 **Live**

### 4. 获取访问地址

1. 在 Dashboard 中点击 **piecework-api** 服务
2. 在页面顶部复制 **URL**（如 `https://piecework-api-xxxx.onrender.com`）
3. 在浏览器中访问该 URL 即可使用计件系统

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
