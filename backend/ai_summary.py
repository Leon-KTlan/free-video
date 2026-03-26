"""
AI 视频摘要模块
- 用 yt-dlp 提取字幕
- 用 DeepSeek 生成摘要 / 要点 / 章节 / 思维导图数据
- 提供 AI 问答（限定在视频内容范围内）
"""
import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

from openai import OpenAI

# ── DeepSeek 客户端 ──────────────────────────────────────
_client: Optional[OpenAI] = None
_subtitle_cache: dict = {}   # url -> subtitle_text，同进程复用


def init_deepseek(api_key: str):
    global _client
    _client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


# ── 字幕提取 ─────────────────────────────────────────────

def _ytdlp_bin() -> str:
    # 兼容从 backend/ 或项目根目录启动的两种情况
    candidates = [
        Path(__file__).parent.parent / "venv" / "bin" / "yt-dlp",  # backend/ 启动
        Path("venv/bin/yt-dlp").resolve(),                          # 根目录启动
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return "yt-dlp"  # fallback: 系统 PATH


def _detect_proxy() -> str:
    try:
        out = subprocess.check_output(["scutil", "--proxy"], timeout=3, text=True)
        host_m = re.search(r"HTTPProxy\s*:\s*(\S+)", out)
        port_m = re.search(r"HTTPPort\s*:\s*(\d+)", out)
        enable_m = re.search(r"HTTPEnable\s*:\s*(\d+)", out)
        if host_m and port_m and enable_m and enable_m.group(1) == "1":
            return f"http://{host_m.group(1)}:{port_m.group(1)}"
    except Exception:
        pass
    return ""


PROXY = _detect_proxy()
YTDLP_BASE = [
    "--no-check-certificate",
    "--no-warnings",
    "--legacy-server-connect",
]


def _fetch_bilibili_subtitle(url: str) -> str:
    """
    通过 B站官方 API 获取 AI 字幕。
    步骤：网页提取 cid -> 调用 /x/player/v2 API -> 下载字幕 JSON
    """
    import ssl
    ssl_ctx = ssl._create_unverified_context()

    if PROXY:
        proxy_h = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
        opener = urllib.request.build_opener(proxy_h)
    else:
        opener = urllib.request.build_opener()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/",
    }

    try:
        # 1. 从 URL 提取 bvid
        bvid_m = re.search(r"(BV[a-zA-Z0-9]+)", url)
        if not bvid_m:
            return ""
        bvid = bvid_m.group(1)

        # 2. 用 view API 获取 cid（正确方式）
        view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = urllib.request.Request(view_url, headers=headers)
        with opener.open(req, timeout=15) as resp:
            view_data = json.loads(resp.read())
        if view_data.get("code") != 0:
            return ""
        cid = view_data.get("data", {}).get("cid")
        if not cid:
            return ""

        # 3. 调用字幕 API
        api_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        req = urllib.request.Request(api_url, headers=headers)
        with opener.open(req, timeout=15) as resp:
            data = json.loads(resp.read())

        subtitles = data.get("data", {}).get("subtitle", {}).get("subtitles", [])
        if not subtitles:
            return ""

        # 优先 ai-zh，其次 zh，再取第一个
        chosen_sub = None
        for pref in ["ai-zh", "zh-CN", "zh"]:
            for s in subtitles:
                if pref in s.get("lan", ""):
                    chosen_sub = s
                    break
            if chosen_sub:
                break
        if not chosen_sub:
            chosen_sub = subtitles[0]

        sub_url = chosen_sub.get("subtitle_url", "")
        if not sub_url:
            return ""
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url

        # 4. 下载字幕 JSON
        req = urllib.request.Request(sub_url, headers=headers)
        with opener.open(req, timeout=15) as resp:
            sub_data = json.loads(resp.read())

        # B站字幕格式: {"body": [{"from": 0.0, "to": 3.0, "content": "文字"}]}
        body = sub_data.get("body", [])
        texts = [item["content"] for item in body if item.get("content", "").strip()]
        return " ".join(texts)

    except Exception:
        return ""


def extract_subtitle(url: str, timeout: int = 120) -> str:
    """
    用 yt-dlp 提取字幕文本。
    策略：
    1. 先尝试带 Cookie（从 Chrome）提取所有语言字幕
    2. 不带 Cookie 重试
    3. 优先中文，其次英文
    返回空字符串表示无字幕。
    """
    if url in _subtitle_cache:
        return _subtitle_cache[url]

    def _try_extract(extra_args: list) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [_ytdlp_bin()]
            if PROXY:
                cmd += ["--proxy", PROXY]
            cmd += YTDLP_BASE + [
                "--write-sub",
                "--write-auto-sub",
                "--sub-langs", "all",   # 下载所有语言字幕
                "--sub-format", "vtt/best",
                "--skip-download",
                "--no-playlist",
                "-o", str(Path(tmpdir) / "sub"),
            ] + extra_args + [url]
            env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}
            subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, env=env)

            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if not vtt_files:
                return ""

            # 优先级：zh-Hans > zh > zh-CN > ai-zh > en > 其他
            priority_keywords = ["zh-Hans", "zh-CN", ".zh.", "-zh", "ai-zh", ".en.", "-en", "en-US"]
            chosen = None
            for kw in priority_keywords:
                for f in vtt_files:
                    if kw.lower() in f.name.lower():
                        chosen = f
                        break
                if chosen:
                    break
            if not chosen:
                # 排除弹幕文件（danmaku），取第一个
                non_danmaku = [f for f in vtt_files if "danmaku" not in f.name.lower()]
                chosen = non_danmaku[0] if non_danmaku else vtt_files[0]

            raw = chosen.read_text(encoding="utf-8", errors="ignore")
            return _parse_vtt(raw)

    # 策略1：尝试从 Chrome 读取 Cookie
    text = ""
    try:
        print(f"[subtitle] 策略1: 带 Chrome Cookie 提取 {url[:60]}")
        text = _try_extract(["--cookies-from-browser", "chrome"], "chrome-cookie")
    except Exception as e:
        print(f"[subtitle] 策略1 失败: {e}")

    # 策略2：不带 Cookie 重试
    if not text.strip():
        try:
            print(f"[subtitle] 策略2: 不带 Cookie 提取")
            text = _try_extract([], "no-cookie")
        except Exception as e:
            print(f"[subtitle] 策略2 失败: {e}")

    # 策略3：B站专用 API
    if not text.strip() and ("bilibili.com" in url or "b23.tv" in url):
        try:
            print(f"[subtitle] 策略3: B站 API 提取")
            text = _fetch_bilibili_subtitle(url)
            print(f"[subtitle] B站 API 结果长度: {len(text)}")
        except Exception as e:
            print(f"[subtitle] 策略3 失败: {e}")

    print(f"[subtitle] 最终字幕长度: {len(text)}")
    _subtitle_cache[url] = text
    return text


def _parse_vtt(vtt: str) -> str:
    """从 VTT 字幕提取纯文本，去重去时间戳，保留顺序"""
    lines = vtt.splitlines()
    texts = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if re.match(r"\d{2}:\d{2}", line):   # 时间戳
            continue
        if re.match(r"^\d+$", line):          # 序号
            continue
        text = re.sub(r"<[^>]+>", "", line).strip()
        if text and text not in seen:
            seen.add(text)
            texts.append(text)
    return " ".join(texts)


# ── DeepSeek 调用 ────────────────────────────────────────

SYSTEM_PROMPT = """\
你是一名专业的视频内容分析师。根据用户提供的视频字幕文本，生成结构化学习摘要。

⚠️ 约束（必须严格遵守）：
1. 所有回答必须严格基于字幕文本，不得虚构或补充字幕中没有的信息。
2. 若字幕不足以支撑某项分析，请说明"字幕内容不足"。
3. 只回答与该视频内容直接相关的问题，拒绝回答无关问题。
4. 始终使用中文回答。
"""


def _chat(messages: list, max_tokens: int = 2000) -> str:
    if _client is None:
        raise RuntimeError("DeepSeek 客户端未初始化")
    resp = _client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def generate_summary(title: str, subtitle_text: str) -> dict:
    """
    生成完整摘要，返回结构：
    {
      summary: str,
      keypoints: [str],
      chapters: [{time, title, content}],
      mindmap: {name, children: [{name, children:[{name}]}]}
    }
    """
    # 字幕超长时截断（DeepSeek 上下文 64k，留余量）
    MAX_CHARS = 12000
    text = subtitle_text[:MAX_CHARS]
    if len(subtitle_text) > MAX_CHARS:
        text += "\n[字幕过长，已截断至前 12000 字]\n"

    prompt = f"""视频标题：{title}

字幕内容：
{text}

请按以下 JSON 格式输出，不要输出任何多余文字：
{{
  "summary": "100字以内的一句话核心概述",
  "keypoints": [
    "要点1",
    "要点2",
    "要点3",
    "要点4",
    "要点5"
  ],
  "chapters": [
    {{"time": "00:00", "title": "章节标题", "content": "该章节内容概括（30字内）"}}
  ],
  "mindmap": {{
    "name": "视频核心主题",
    "children": [
      {{
        "name": "一级节点",
        "children": [
          {{"name": "二级知识点"}},
          {{"name": "二级知识点"}}
        ]
      }}
    ]
  }}
}}

要求：
- chapters 按视频进度合理分段，3-8个章节
- mindmap 提炼核心知识结构，2-4个一级节点，每节点2-4个子节点
- 所有内容严格来自字幕，不虚构
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    raw = _chat(messages, max_tokens=2500)

    # 提取 JSON
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise ValueError(f"DeepSeek 返回格式异常: {raw[:200]}")
    result = json.loads(json_match.group())
    return result


def chat_with_video(title: str, subtitle_text: str,
                   history: list, user_question: str) -> str:
    """
    基于视频字幕的 AI 问答。
    history: [{role: 'user'|'assistant', content: str}]  最近 N 轮
    """
    MAX_CHARS = 10000
    text = subtitle_text[:MAX_CHARS]
    if len(subtitle_text) > MAX_CHARS:
        text += "\n[字幕过长，已截断]\n"

    system_with_context = (
        SYSTEM_PROMPT
        + f"\n\n以下是视频《{title}》的字幕内容，请基于此回答问题：\n\n"
        + text
    )

    messages = [{"role": "system", "content": system_with_context}]
    # 保留最近 6 轮历史避免超长
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_question})

    return _chat(messages, max_tokens=800)
