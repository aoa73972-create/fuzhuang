# Render 服务 URL 查找说明

## 第一步：进入主控制台

1. 打开 https://dashboard.render.com
2. 登录后，你会看到**服务列表**（可能显示为 Dashboard 或 Home）

---

## 第二步：找到 piecework-api 服务

在页面中查找名为 **piecework-api** 的卡片/行，点击进入。

> 如果列表为空，说明还没部署成功，需要先完成 Blueprint 部署。

---

## 第三步：在服务详情页找 URL

进入 piecework-api 后，URL 通常出现在以下位置之一：

### 位置 A：页面顶部（最常见）
- 在**服务名称 "piecework-api"** 下方或右侧
- 有一行可点击的链接，格式类似：`https://piecework-api-xxxx.onrender.com`
- 旁边可能有**复制图标**（📋）或 "Open" 按钮

### 位置 B：顶部导航栏
- 页面最上方可能有一个**链接/按钮**，写着 "Open live site" 或直接显示 URL

### 位置 C：左侧或右侧信息栏
- 在 **Info**、**Overview** 或类似区域
- 显示 "URL" 或 "Web Service URL"

### 位置 D：Settings 页面
- 点击左侧 **Settings**
- 在 **Custom Domains** 区域，会显示默认的 `xxx.onrender.com` 地址

---

## URL 格式

你的后端 URL 格式为：
```
https://piecework-api-随机字符.onrender.com
```
或
```
https://piecework-api.onrender.com
```

**注意**：不要加末尾斜杠 `/`，复制完整地址即可。

---

## 如果实在找不到

可以尝试直接访问（服务名为 piecework-api 时）：
- https://piecework-api.onrender.com

若无法访问，说明 Render 分配了带随机后缀的地址，仍需在控制台中找到。
