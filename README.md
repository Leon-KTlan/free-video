# VideoSnap — 万能视频下载 + AI 摘要

> 基于 **yt-dlp + FastAPI + Vue 3** 构建，支持 B站、YouTube、抖音、Twitter 等 1800+ 平台一键解析下载，并提供 AI 视频摘要功能。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 后端 | FastAPI + uvicorn (Python 3.9+) |
| 下载引擎 | yt-dlp 2025.10.14 |
| 进度推送 | Server-Sent Events (SSE) |
| AI 摘要 | DeepSeek Chat API |
| 字幕提取 | yt-dlp（公开字幕） |

---

## 功能特性

### 视频下载
- **多平台支持**：YouTube、B站、抖音、Twitter/X、Instagram、TikTok 等 1800+
- **多画质选择**：1080p / 720p / 480p / 360p / 最佳画质
- **有声音的 mp4**：自动检测 ffmpeg，分离流自动合并视频+音频
- **封面预览**：后端代理封面图，解决防盗链
- **实时进度**：SSE 推送下载进度、速度、剩余时间
- **代理自适应**：自动读取 macOS 系统代理，无需手动配置

### AI 视频摘要（新功能）
- **一键摘要**：提取视频字幕，DeepSeek 生成结构化摘要
- **4 个维度展示**：总结 / 字幕原文 / 思维导图 / AI 问答
- **支持平台**：YouTube（有 CC 字幕）、TED、Coursera 等
- **B站暂不支持**：B站字幕需登录获取，暂不支持
- **AI 问答**：严格基于视频字幕内容回答，不虚构

---

## 快速启动

### 依赖安装

```bash
# Python 依赖
python3 -m venv venv
venv/bin/pip install -r backend/requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# ffmpeg（合并分离流必须）
brew install ffmpeg
```

### 配置 AI 摘要

在 `backend/app.py` 中配置 DeepSeek Key（已内置，可替换）：
```python
_DEEPSEEK_KEY = "sk-your-deepseek-key"
```

### 启动服务

> ⚠️ 必须在系统终端（iTerm/Terminal.app）运行，不要用 Cursor 内置终端

```bash
# 方式一：一键启动
bash start.sh

# 方式二：手动启动
# 终端 1 — 后端
cd backend && ../venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 终端 2 — 前端
cd frontend && npm run dev
```

### 访问

| 地址 | 说明 |
|------|------|
| http://localhost:5173 | 前端页面 |
| http://localhost:8000/api/health | 后端状态 |
| http://localhost:8000/api/v2/subtitle-status | 字幕能力状态 |

---

## 使用流程

### 视频下载
1. 粘贴视频链接 → 点击「解析」
2. 查看封面、标题、时长
3. 选择画质 → 点击「开始下载」
4. 实时查看进度 → 下载完成点击「保存文件」

### AI 摘要（YouTube 等有字幕视频）
1. 解析视频后点击「AI 摘要」按钮
2. 等待约 20-40 秒
3. 查看四个维度：
   - **总结**：一句话概述 + 核心要点
   - **字幕**：完整字幕原文
   - **导图**：思维导图
   - **问答**：针对视频内容提问

---

## 项目结构

```
free-video/
├── backend/
│   ├── app.py                  # FastAPI 主应用
│   ├── subtitle_extractor.py   # 字幕提取模块（新）
│   ├── video_summarizer.py     # AI 摘要模块（新）
│   ├── ai_summary.py           # 旧版 AI 摘要（保留兼容）
│   ├── auth.py                 # 用户认证
│   ├── models.py               # 数据库模型
│   ├── payment.py              # 支付模块
│   ├── plans.py                # 套餐配置
│   ├── requirements.txt        # Python 依赖
│   └── SUBTITLE_SETUP.md       # 字幕配置说明
├── frontend/
│   └── src/
│       ├── App.vue             # 根组件
│       └── components/
│           ├── MainCard.vue    # 核心交互卡片
│           ├── VideoSummary.vue # AI 摘要面板（新）
│           ├── AISummary.vue   # 旧版摘要面板
│           ├── Header.vue
│           ├── Features.vue
│           ├── Pricing.vue
│           ├── Platforms.vue
│           └── Footer.vue
├── start.sh                    # 一键启动
└── README.md
```

---

## API 说明

### 新版 AI 摘要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v2/summarize` | POST | 提取字幕 + 生成摘要 |
| `/api/v2/chat` | POST | 基于字幕的 AI 问答 |
| `/api/v2/subtitle-status` | GET | 字幕提取能力状态 |

```json
// POST /api/v2/summarize
{ "url": "https://...", "title": "视频标题" }

// 返回
{
  "success": true,
  "summary": "核心概述",
  "keypoints": ["要点1", "要点2"],
  "chapters": [{"time": "00:00", "title": "章节", "content": "..."}],
  "mindmap": {"name": "主题", "children": [...]},
  "transcript": "完整字幕文本"
}
```

### 字幕支持状态

| 平台 | 状态 | 说明 |
|------|------|------|
| YouTube | ✅ | 有 CC 字幕（手动/自动）均可 |
| TED | ✅ | 官方字幕 |
| Coursera | ✅ | 课程字幕 |
| B站 | ❌ | 需登录，暂不支持 |
| 抖音 | ❌ | 无公开字幕 |

---

## 关键技术说明

### 字幕提取策略
1. yt-dlp 提取公开字幕（VTT 格式）
2. 优先级：手动中文 > 手动英文 > 自动中文 > 自动英文
3. B站直接返回不支持提示

### 代理自动检测
后端通过 `scutil --proxy` 读取 macOS 系统代理，自动传给 yt-dlp，支持 Clash、V2Ray 等任意代理工具。

### 分离流合并
B站等平台视频流和音频流分离：
- **有 ffmpeg**：自动合并为有声音的 mp4
- **无 ffmpeg**：降级为合流格式

安装：`brew install ffmpeg`

---

## 常见问题

**Q: B站 AI 摘要为什么不支持？**
A: B站字幕文件需要登录态 Cookie 才能获取，未登录时 API 返回空列表。技术上可行但需要用户提供 SESSDATA，暂未实现。

**Q: YouTube 有字幕但摘要失败？**
A: 确认视频播放器有 CC 按钮，且网络代理正常（后端需要能访问 YouTube）。

**Q: B站下载后视频没有声音？**
A: 需要安装 ffmpeg：`brew install ffmpeg`，然后重启后端。

**Q: 为什么不能在 Cursor 内置终端运行？**
A: Cursor IDE 沙盒屏蔽了视频平台请求，必须在系统终端（iTerm/Terminal.app）启动。

**Q: 手机如何访问？**
A: 同一 WiFi 下访问 `http://[电脑IP]:5173`，查询 IP：`ipconfig getifaddr en0`

---

> 本工具仅供个人学习研究使用，请尊重版权，遵守所在地区法律法规。
