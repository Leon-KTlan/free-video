# VideoSnap — 万能视频下载器

> 基于 **yt-dlp + FastAPI + Vue 3** 构建，支持 B站、YouTube、抖音、Twitter 等 1800+ 平台一键解析下载。

---

## 技术栈

| 层次 | 技术 |
|------|---------|
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 后端 | FastAPI + uvicorn (Python 3.9+) |
| 下载引擎 | yt-dlp 2025.10.14 |
| 进度推送 | Server-Sent Events (SSE) |
| 封面代理 | FastAPI 后端代理（解决防盗链）|

---

## 功能特性

- **多平台支持**：YouTube、B站、抖音、Twitter/X、Instagram、TikTok 等 1800+
- **多画质选择**：1080p / 720p / 480p / 360p / 最佳画质
- **有声音的 mp4**：自动检测 ffmpeg，分离流自动合并视频+音频
- **封面预览**：后端代理封面图，解决防盗链
- **实时进度**：SSE 推送下载进度、速度、剩余时间
- **代理自适应**：自动读取 macOS 系统代理（`scutil --proxy`），无需手动配置
- **SSL 修复**：`--legacy-server-connect` 修复 B站等平台的 SSL EOF 错误
- **错误友好提示**：403/404/SSL/ffmpeg 缺失等均有中文说明

---

## 快速启动

### 依赖安装

```bash
# Python 依赖
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# ffmpeg（合并 B站等平台分离流必须）
brew install ffmpeg
```

### 启动服务

> ⚠️ 必须在系统终端（iTerm/Terminal.app）运行，不要用 Cursor 内置终端

```bash
# 方式一：一键启动脚本
bash start.sh

# 方式二：手动启动
# 终端 1 — 后端
venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 终端 2 — 前端
cd frontend && npm run dev
```

### 访问

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8000/api/health | 后端状态（含代理/ffmpeg 检测结果）|

---

## 使用流程

1. 复制视频链接（B站 / YouTube / 抖音 / Twitter 等）
2. 粘贴到输入框，点击「解析」
3. 查看封面、标题、时长
4. 从格式列表选择画质
5. 点击「开始下载」，实时查看进度条
6. 下载完成后点击「保存文件」

---

## 项目结构

```
free-video/
├── app.py                  # FastAPI 后端（解析/下载/进度/封面代理）
├── requirements.txt        # Python 依赖
├── test_api.py             # API 测试脚本
├── start.sh                # 一键启动脚本
├── run_backend.sh          # 仅启动后端
├── downloads/              # 视频下载目录（自动创建）
└── frontend/
    ├── src/
    │   ├── App.vue
    │   ├── style.css
    │   └── components/
    │       ├── Header.vue      # 顶部导航
    │       ├── MainCard.vue    # 核心卡片（输入→格式→进度→完成）
    │       ├── Stats.vue       # 平台统计
    │       ├── Features.vue    # 功能介绍
    │       ├── Platforms.vue   # 支持平台展示
    │       └── Footer.vue      # 底部 FAQ
    ├── vite.config.js          # Vite 配置（/api 代理→8000）
    ├── tailwind.config.js
    └── package.json
```

---

## 关键技术说明

### 代理自动检测
后端启动时通过 `scutil --proxy` 读取 macOS 系统代理，自动传给 yt-dlp。
无需手动设置，支持 Clash、V2Ray 等任意代理工具。

### 分离流合并（需要 ffmpeg）
B站等平台的视频流和音频流是分开的（分离流）。
- **有 ffmpeg**：下载 `视频流+bestaudio` 并自动合并为 mp4（有声音）
- **无 ffmpeg**：降级为平台提供的合流格式（画质较低但有声音）

安装 ffmpeg：`brew install ffmpeg`

### subprocess 调用 yt-dlp
Python 3.9 与 yt-dlp 最新版存在兼容性问题（yt-dlp 已弃用 3.9 支持）。
后端改用 `subprocess` 直接调用 `venv/bin/yt-dlp` CLI，完全绕过该问题。

---

## 常见问题

**Q: B站下载后视频没有声音 / 格式是 m4a？**
A: 没有安装 ffmpeg。运行 `brew install ffmpeg` 后重启后端即可。

**Q: 解析失败，提示 403？**
A: 该视频有地区限制或需要登录。可在 `app.py` 中配置 `--cookies-from-browser chrome`。

**Q: YouTube 提示需要登录验证？**
A: YouTube 对自动化访问限制增强。用 `--cookies-from-browser chrome` 传入浏览器 Cookie。

**Q: 为什么不能在 Cursor 内置终端运行？**
A: Cursor IDE 沙盒有独立代理（127.0.0.1:52671），会屏蔽视频平台请求。
系统终端直接使用系统代理（如 Clash 的 7897 端口），可正常访问。

**Q: 手机如何访问？**
A: 确保手机和电脑在同一 WiFi，访问 `http://[电脑IP]:5173`。
查询电脑 IP：`ipconfig getifaddr en0`

---

> 本工具仅供个人学习研究使用，请尊重版权，遵守所在地区法律法规。
