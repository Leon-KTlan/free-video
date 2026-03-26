"""
SubtitleExtractor —— 字幕提取模块

只提取平台公开提供的字幕（无需登录）：
- YouTube: 有 CC 字幕的视频（手动字幕 > 自动字幕，优先中文）
- 其他支持 yt-dlp 字幕的平台（TED、Coursera 等）

B站暂不支持（B站字幕需要登录才能获取）
"""
import re
import subprocess
import tempfile
from pathlib import Path

# ── 路径 & 代理 ────────────────────────────────────────────
def _ytdlp_bin() -> str:
    candidates = [
        Path(__file__).parent.parent / "venv" / "bin" / "yt-dlp",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return "yt-dlp"


def _detect_proxy() -> str:
    try:
        import subprocess as sp
        out = sp.check_output(["scutil", "--proxy"], timeout=3, text=True)
        host_m = re.search(r"HTTPProxy\s*:\s*(\S+)", out)
        port_m = re.search(r"HTTPPort\s*:\s*(\d+)", out)
        enable_m = re.search(r"HTTPEnable\s*:\s*(\d+)", out)
        if host_m and port_m and enable_m and enable_m.group(1) == "1":
            return f"http://{host_m.group(1)}:{port_m.group(1)}"
    except Exception:
        pass
    return ""


PROXY = _detect_proxy()
YTDLP_BASE = ["--no-check-certificate", "--no-warnings", "--legacy-server-connect"]

# 进程内缓存
_cache: dict = {}


def _is_bilibili(url: str) -> bool:
    return "bilibili.com" in url or "b23.tv" in url


def _parse_vtt(vtt: str) -> str:
    """VTT 转纯文本，去重去时间戳"""
    lines = vtt.splitlines()
    texts, seen = [], set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("X-TIMESTAMP"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line):
            continue
        # 去掉 VTT 内联标签
        text = re.sub(r"<[^>]+>", "", line).strip()
        if text and text not in seen:
            seen.add(text)
            texts.append(text)
    return " ".join(texts)


def extract(url: str) -> tuple[str, str]:
    """
    提取视频公开字幕。
    返回 (subtitle_text, method)
    method: 'subtitle' | 'auto_caption' | ''
    B站直接返回 ('', 'unsupported')
    """
    if url in _cache:
        print(f"[SubtitleExtractor] 命中缓存")
        return _cache[url]

    # B站明确不支持
    if _is_bilibili(url):
        print(f"[SubtitleExtractor] B站暂不支持字幕提取")
        result = ("", "unsupported")
        _cache[url] = result
        return result

    print(f"[SubtitleExtractor] 提取字幕: {url[:80]}")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [_ytdlp_bin()]
        if PROXY:
            cmd += ["--proxy", PROXY]
        cmd += YTDLP_BASE + [
            "--write-sub",       # 手动字幕
            "--write-auto-sub",  # 自动字幕（YouTube 自动生成）
            "--sub-langs", "zh-Hans,zh-CN,zh,en,en-US,en-GB",
            "--sub-format", "vtt/best",
            "--skip-download",
            "--no-playlist",
            "-o", str(Path(tmpdir) / "sub"),
            url,
        ]
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
        except subprocess.TimeoutExpired:
            print(f"[SubtitleExtractor] 超时")
            result = ("", "")
            _cache[url] = result
            return result

        all_files = list(Path(tmpdir).iterdir())
        vtt_files = [f for f in all_files if f.suffix == ".vtt"]
        print(f"[SubtitleExtractor] 文件: {[f.name for f in all_files]}")

        if not vtt_files:
            print(f"[SubtitleExtractor] 无字幕文件")
            result = ("", "")
            _cache[url] = result
            return result

        # 优先级：手动中文 > 手动英文 > 自动中文 > 自动英文
        priority = ["zh-Hans", "zh-CN", "-zh", "zh", "en-US", "en-GB", "-en", "en"]
        # 区分手动字幕（不含 orig）和自动字幕（含 orig 或 auto）
        manual = [f for f in vtt_files if "orig" not in f.name.lower() and "auto" not in f.name.lower()]
        auto   = [f for f in vtt_files if f not in manual]

        chosen = None
        method = ""
        for pool, m in [(manual, "subtitle"), (auto, "auto_caption")]:
            for kw in priority:
                for f in pool:
                    if kw.lower() in f.name.lower():
                        chosen = f
                        method = m
                        break
                if chosen:
                    break
            if chosen:
                break

        if not chosen:
            chosen = vtt_files[0]
            method = "subtitle"

        print(f"[SubtitleExtractor] 选择: {chosen.name} ({method})")
        text = _parse_vtt(chosen.read_text(encoding="utf-8", errors="ignore"))
        print(f"[SubtitleExtractor] 字幕长度: {len(text)}")

        result = (text, method)
        _cache[url] = result
        return result


def is_supported(url: str) -> bool:
    """是否是支持字幕提取的平台"""
    return not _is_bilibili(url)


def unsupported_reason(url: str) -> str:
    """返回不支持的原因提示"""
    if _is_bilibili(url):
        return "B站字幕需要登录才能获取，暂不支持。建议使用 YouTube、TED 等有公开字幕的视频。"
    return ""
