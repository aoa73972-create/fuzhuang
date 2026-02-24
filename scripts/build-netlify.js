#!/usr/bin/env node
/**
 * Netlify 构建脚本：将前端静态文件复制到 public 目录，并注入 API 地址
 * 环境变量 VITE_API_URL 或 API_URL 指定后端地址
 */
const fs = require('fs');
const path = require('path');

const API_URL = process.env.API_URL || process.env.VITE_API_URL || '';
const ROOT = path.join(__dirname, '..');
const PUBLIC = path.join(ROOT, 'public');

// 清空并创建 public 目录
if (fs.existsSync(PUBLIC)) fs.rmSync(PUBLIC, { recursive: true });
fs.mkdirSync(PUBLIC, { recursive: true });

// 复制 static 目录
const staticDir = path.join(ROOT, 'static');
fs.cpSync(staticDir, path.join(PUBLIC, 'static'), { recursive: true });

// 生成 config.js（注入 API 地址）
const configJs = `window.API_BASE = ${JSON.stringify(API_URL.replace(/\/$/, ''))};\n`;
fs.writeFileSync(path.join(PUBLIC, 'config.js'), configJs);

// 复制并处理 index.html
let html = fs.readFileSync(path.join(ROOT, 'templates', 'index.html'), 'utf8');
// 确保 config.js 在 static 之前加载
if (!html.includes('config.js')) {
  html = html.replace('<script src="/static/dayjs', '<script src="/config.js"></script>\n  <script src="/static/dayjs');
}
fs.writeFileSync(path.join(PUBLIC, 'index.html'), html);

console.log('Netlify build done. API_BASE =', API_URL || '(same origin)');
