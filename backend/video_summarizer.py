"""
VideoSummarizer —— AI 视频摘要模块（新版）

基于 subtitle_extractor 提取字幕，调用 DeepSeek 生成：
- summary: 一句话概述
- keypoints: 核心要点列表
- chapters: 章节时间轴
- mindmap: 思维导图数据
- transcript: 完整字幕文本

同时提供 AI 问答（基于字幕内容，严格限定范围）。
"""
import json
import re
from typing import Generator, Optional

from openai import OpenAI

# DeepSeek 客户端（由 app.py 统一初始化后注入）
_client: Optional[OpenAI] = None


def set_client(client: OpenAI):
    """注入 DeepSeek 客户端（由 app.py 调用）"""
    global _client
    _client = client


def _get_client() -> OpenAI:
    if _client is None:
        raise RuntimeError("VideoSummarizer: DeepSeek 客户端未初始化，请先调用 set_client()")
    return _client


# ── System Prompt ─────────────────────────────────────────
SYSTEM_PROMPT = """\
你是一名专业的视频内容分析师。根据用户提供的视频字幕文本，生成结构化学习摘要。

⚠️ 约束（必须严格遵守）：
1. 所有回答必须严格基于字幕文本，不得虚构或补充字幕中没有的信息。
2. 若字幕内容不足以支撑某项分析，请如实说明"字幕内容不足"。
3. 只回答与该视频内容直接相关的问题，拒绝回答无关问题。
4. 始终使用中文回答。
"""

MAX_SUBTITLE_CHARS = 12000  # DeepSeek 上下文限制内留余量


def _truncate(text: str, max_chars: int = MAX_SUBTITLE_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[字幕过长，已截断]"


def _chat(messages: list, max_tokens: int = 2000) -> str:
    resp = _get_client().chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def generate_summary(title: str, subtitle_text: str) -> dict:
    """
    生成完整摘要。返回：
    {
      summary, keypoints, chapters, mindmap, transcript
    }
    """
    text = _truncate(subtitle_text)
    prompt = f"""视频标题：{title}

字幕内容：
{text}

请严格按以下 JSON 格式输出，不要输出任何多余文字或 markdown 代码块：
{{
  "summary": "100字以内的一句话核心概述",
  "keypoints": [
    "要点1（基于字幕内容）",
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
- chapters 按内容合理分段，3-8个章节
- mindmap 2-4个一级节点，每节点2-4个子节点
- 所有内容严格来自字幕，不虚构"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    raw = _chat(messages, max_tokens=2500)

    # 提取 JSON（去掉可能的 markdown 包裹）
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    json_m = re.search(r"\{[\s\S]*\}", raw)
    if not json_m:
        raise ValueError(f"DeepSeek 返回格式异常: {raw[:300]}")
    result = json.loads(json_m.group())
    result["transcript"] = subtitle_text  # 附带完整字幕
    return result


def chat(title: str, subtitle_text: str, history: list, question: str) -> str:
    """
    基于字幕的 AI 问答。
    history: [{role, content}]  最近几轮
    """
    text = _truncate(subtitle_text, 10000)
    system = (
        SYSTEM_PROMPT
        + f"\n\n以下是视频《{title}》的字幕内容，请严格基于此回答问题：\n\n{text}"
    )
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:  # 最近 6 轮
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})
    return _chat(messages, max_tokens=800)
