import json
import asyncio
import threading
import re
import ssl
import subprocess
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, Response
from pydantic import BaseModel
import yt_dlp

ssl._create_default_https_context = ssl._create_unverified_context

app = FastAPI(title="VideoSnap API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
download_progress: dict = {}

FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.bilibili.com/",
}

YTDLP_BIN = str(Path("venv/bin/yt-dlp").resolve())


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


YTDLP_BASE_ARGS = [
    "--no-check-certificate",
    "--no-warnings",
    "--legacy-server-connect",   # 修复 B站等平台的 SSL EOF 问题
]


def find_ffmpeg() -> str:
    """查找系统 ffmpeg 路径"""
    for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if Path(p).exists():
            return p
    import shutil
    return shutil.which("ffmpeg") or ""


FFMPEG_PATH = find_ffmpeg()


def run_ytdlp_info(url: str, timeout: int = 60) -> subprocess.CompletedProcess:
    cmd = [YTDLP_BIN]
    if PROXY:
        cmd += ["--proxy", PROXY]
    cmd += YTDLP_BASE_ARGS + ["--dump-single-json", url]
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    return result


def clean_stderr(stderr: str) -> str:
    """过滤掉 Python 版本废弃警告，只保留真正的错误"""
    lines = [l for l in stderr.splitlines()
             if "Deprecated Feature" not in l
             and "Support for Python version" not in l
             and "Please update to Python" not in l]
    return "\n".join(lines).strip()


class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str = "best"
    task_id: str


@app.get("/")
async def root():
    return {"message": "VideoSnap API is running"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "yt_dlp_version": yt_dlp.version.__version__,
        "proxy": PROXY,
        "ffmpeg": FFMPEG_PATH or "not found (install: brew install ffmpeg)",
    }


@app.get("/api/thumbnail")
async def proxy_thumbnail(url: str):
    try:
        req = urllib.request.Request(url, headers=FAKE_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            ct = resp.headers.get("Content-Type", "image/jpeg")
        return Response(content=data, media_type=ct)
    except Exception:
        return Response(
            content=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82",
            media_type="image/png",
        )


@app.post("/api/info")
async def get_video_info(req: InfoRequest):
    try:
        result = run_ytdlp_info(req.url)
        if result.returncode != 0:
            err = clean_stderr(result.stderr or result.stdout)
            if "403" in err or "Forbidden" in err:
                detail = "平台拒绝访问 (403)，视频可能有地区限制或需要登录"
            elif "404" in err:
                detail = "视频不存在或已被删除"
            elif "Private" in err:
                detail = "该视频为私密视频"
            elif "SSL" in err or "EOF" in err:
                detail = "SSL 连接失败，请检查网络或代理设置"
            elif "Connection" in err or "network" in err.lower():
                detail = "网络连接失败，请检查网络"
            else:
                detail = f"解析失败: {err[:300]}"
            raise HTTPException(status_code=400, detail=detail)

        info = json.loads(result.stdout)
        formats_raw = info.get("formats", [])
        formats = []

        # 按分辨率分组，每组选最佳视频流（优先合流 > H.264 > 其他）
        video_by_height: dict = {}
        for f in formats_raw:
            vcodec = f.get("vcodec") or "none"
            acodec = f.get("acodec") or "none"
            ext = f.get("ext", "")
            height = f.get("height")
            has_video = vcodec != "none"
            has_audio = acodec != "none"
            if not has_video or not height:
                continue
            if ext in ("mhtml", "vtt", "json", "none"):
                continue
            score = (2 if has_audio else 0) + (1 if "avc1" in vcodec else 0)
            prev = video_by_height.get(height)
            if prev is None:
                video_by_height[height] = (score, f)
            else:
                if score > prev[0]:
                    video_by_height[height] = (score, f)

        for height in sorted(video_by_height.keys(), reverse=True):
            _, f = video_by_height[height]
            fid = f.get("format_id", "")
            acodec = f.get("acodec") or "none"
            has_audio = acodec != "none"
            filesize = f.get("filesize") or f.get("filesize_approx")
            tbr = f.get("tbr") or 0
            size_str = f"{filesize/1024/1024:.1f} MB" if filesize else (f"~{int(tbr)}kbps" if tbr else "")

            if has_audio:
                dl_fid = fid                              # 合流，直接下载
            elif FFMPEG_PATH:
                dl_fid = f"{fid}+bestaudio/best"          # 有 ffmpeg，合并音频
            else:
                dl_fid = f"best[height<={height}]/best"   # 无 ffmpeg，退回合流兜底

            formats.append({"format_id": dl_fid, "label": f"{height}p",
                             "ext": "mp4", "type": "video+audio",
                             "size": size_str, "height": height})

        # 推荐选项放最前
        best_fid = "bestvideo+bestaudio/best" if FFMPEG_PATH else "best"
        formats.insert(0, {"format_id": best_fid, "label": "最佳画质（推荐）",
                           "ext": "mp4", "type": "video+audio", "size": "", "height": 99999})

        # 没解析到任何格式时的通用兜底
        if len(formats) == 1:
            for h in [1080, 720, 480, 360]:
                fid = f"bestvideo[height<={h}]+bestaudio/best" if FFMPEG_PATH else f"best[height<={h}]/best"
                formats.append({"format_id": fid, "label": f"{h}p",
                                 "ext": "mp4", "type": "video+audio", "size": "", "height": h})

        thumbnail = info.get("thumbnail", "")
        from urllib.parse import quote
        thumbnail_proxy = f"/api/thumbnail?url={quote(thumbnail)}" if thumbnail else ""

        return {
            "title": info.get("title", "未知标题"),
            "thumbnail": thumbnail_proxy,
            "duration": info.get("duration") or 0,
            "uploader": info.get("uploader") or info.get("channel") or "",
            "platform": info.get("extractor_key", ""),
            "formats": formats,
            "webpage_url": info.get("webpage_url", req.url),
        }

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="解析超时，请稍后重试")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="解析响应格式异常")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)[:200]}")


def do_download(url: str, format_id: str, task_id: str, output_path: Path):
    download_progress[task_id] = {
        "status": "downloading", "percent": 0,
        "speed": "", "eta": "", "filename": "", "error": "",
    }
    cmd = [YTDLP_BIN]
    if PROXY:
        cmd += ["--proxy", PROXY]
    if FFMPEG_PATH:
        cmd += ["--ffmpeg-location", FFMPEG_PATH]
    cmd += YTDLP_BASE_ARGS + [
        "-f", format_id,
        "-o", str(output_path / "%(title).80s.%(ext)s"),
        "--merge-output-format", "mp4",
        "--newline",
        url,
    ]
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env=env
        )
        for line in proc.stdout:
            line = line.strip()
            m = re.search(r"\[download\]\s+(\d+\.?\d*)%.*?at\s+(\S+).*?ETA\s+(\S+)", line)
            if m:
                download_progress[task_id].update({
                    "status": "downloading",
                    "percent": float(m.group(1)),
                    "speed": m.group(2),
                    "eta": m.group(3),
                })
            elif "[download] 100%" in line or "Merging formats" in line or "Destination" in line:
                download_progress[task_id].update({"status": "processing", "percent": 99})
        proc.wait()
        if proc.returncode != 0:
            raise Exception(f"yt-dlp 退出码: {proc.returncode}")
        files = sorted(output_path.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            raise Exception("未找到下载文件")
        actual = files[0]
        download_progress[task_id].update({
            "status": "done", "percent": 100,
            "filename": actual.name,
            "download_url": f"/api/file/{task_id}/{actual.name}",
        })
    except Exception as e:
        err = str(e)
        if "403" in err:
            friendly = "平台拒绝下载 (403)，请尝试其他画质"
        elif "503" in err:
            friendly = "平台服务暂时不可用，请稍后重试"
        elif "ffmpeg" in err.lower():
            friendly = "需要 ffmpeg 合并视频，请运行: brew install ffmpeg"
        else:
            friendly = err[:300]
        download_progress[task_id].update({"status": "error", "error": friendly})


@app.post("/api/download")
async def start_download(req: DownloadRequest):
    task_dir = DOWNLOAD_DIR / req.task_id
    task_dir.mkdir(exist_ok=True)
    thread = threading.Thread(
        target=do_download,
        args=(req.url, req.format_id, req.task_id, task_dir),
        daemon=True,
    )
    thread.start()
    return {"task_id": req.task_id, "status": "started"}


@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    async def event_generator():
        for _ in range(600):
            progress = download_progress.get(task_id, {"status": "pending", "percent": 0})
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
            if progress.get("status") in ("done", "error"):
                break
            await asyncio.sleep(0.8)
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/file/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    file_path = DOWNLOAD_DIR / task_id / filename
    if not file_path.exists():
        task_dir = DOWNLOAD_DIR / task_id
        if task_dir.exists():
            files = list(task_dir.iterdir())
            if files:
                file_path = files[0]
                filename = file_path.name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
