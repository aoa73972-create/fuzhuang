# Netlify 无服务器部署指南

前端部署到 Netlify（静态托管，无服务器）。支持两种模式：

- **纯前端模式**：不配置 API_URL，数据保存在浏览器 localStorage
- **前后端分离**：配置 API_URL 指向后端，数据保存在服务器

---

## 前置条件

1. 代码已推送到 **GitHub**（https://github.com/aoa73972-create/fuzhuang）
2. 已有 [Netlify](https://netlify.com) 账号（可用 GitHub 登录）

---

## 部署步骤

### 1. 打开 Netlify

在浏览器访问：**https://app.netlify.com**

### 2. 导入项目

1. 点击 **Add new site** → **Import an existing project**
2. 选择 **GitHub**，授权 Netlify 访问
3. 在仓库列表中选择 **aoa73972-create/fuzhuang**

### 3. 配置构建

Netlify 会自动读取 `netlify.toml`，默认配置为：

| 配置项 | 值 |
|--------|-----|
| Build command | `npm run build:netlify` |
| Publish directory | `public` |

### 4. 环境变量（可选）

- **不配置 API_URL**：纯前端模式，数据保存在浏览器 localStorage，无需后端
- **配置 API_URL**：指向后端地址（如 `https://piecework-api-xxxx.onrender.com`），数据保存在服务器

### 5. 部署

点击 **Deploy site**，等待约 1–2 分钟完成。

### 6. 访问系统

部署完成后，访问 Netlify 分配的地址即可使用。

---

## 纯前端模式说明

- 数据保存在**当前浏览器**的 localStorage
- 换浏览器或清除数据会丢失
- 无需登录，直接进入系统（默认管理员权限）
- 适合单人/双人本地使用
