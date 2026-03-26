#!/usr/bin/env python3
"""
VideoSnap 本地测试脚本
在你自己的终端运行此脚本验证功能
用法: python3 test_api.py [视频URL]
"""
import sys
import json
import urllib.request
import urllib.parse

BASE = "http://localhost:8000"

def test_health():
    print("[1] 测试后端健康检查...")
    with urllib.request.urlopen(f"{BASE}/api/health", timeout=5) as r:
        data = json.load(r)
    print(f"    yt-dlp 版本: {data['yt_dlp_version']}  ✓")

def test_info(url):
    print(f"\n[2] 解析视频信息: {url[:60]}...")
    body = json.dumps({"url": url}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/info",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    print(f"    标题     : {data['title'][:60]}")
    print(f"    上传者   : {data.get('uploader','N/A')}")
    print(f"    时长     : {data.get('duration','N/A')}秒")
    print(f"    平台     : {data.get('platform','N/A')}")
    print(f"    封面URL  : {'有' if data.get('thumbnail') else '无'}")
    print(f"    格式数量 : {len(data.get('formats',[]))}")
    print("\n    可用格式列表:")
    for f in data.get('formats', [])[:8]:
        print(f"      [{f['type']:12}] {f['label']:15} {f['ext']:5} {f.get('size',''):10} id={f['format_id']}")
    return data

def test_download(url, fmt_id, task_id="test001"):
    print(f"\n[3] 开始下载 format_id={fmt_id}...")
    body = json.dumps({"url": url, "format_id": fmt_id, "task_id": task_id}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/download",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    print(f"    下载任务已启动: {data}")

    print("    监听下载进度 (SSE)...")
    import time
    for _ in range(300):
        with urllib.request.urlopen(f"{BASE}/api/progress/{task_id}", timeout=5) as r:
            line = r.readline().decode().strip()
            if line.startswith("data:"):
                prog = json.loads(line[5:])
                status = prog.get('status')
                pct = prog.get('percent', 0)
                speed = prog.get('speed', '')
                print(f"    {status:12} {pct:5.1f}% {speed}", end='\r')
                if status == 'done':
                    print(f"\n    下载完成! 文件: {prog.get('filename')}  ✓")
                    print(f"    下载链接: {BASE}{prog.get('download_url')}")
                    return prog
                elif status == 'error':
                    print(f"\n    下载失败: {prog.get('error')}")
                    return prog
        time.sleep(1)

if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.bilibili.com/video/BV1GJ411x7h7"
    try:
        test_health()
        info = test_info(test_url)
        if info.get('formats'):
            fmt_id = info['formats'][0]['format_id']
            test_download(test_url, fmt_id)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
