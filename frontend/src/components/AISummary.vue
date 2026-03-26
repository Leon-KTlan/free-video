<template>
  <div class="ai-summary-panel">
    <!-- 标签页切换 -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs" :key="tab.id"
        class="tab-btn" :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- 概述 -->
    <div v-if="activeTab === 'summary'" class="tab-pane">
      <div class="section-card">
        <div class="section-label">核心概述</div>
        <p class="summary-text">{{ data.summary }}</p>
      </div>
      <div class="section-card mt-4">
        <div class="section-label">核心要点</div>
        <ul class="keypoints-list">
          <li v-for="(kp, i) in data.keypoints" :key="i" class="keypoint-item">
            <span class="keypoint-num">{{ i + 1 }}</span>
            <span class="keypoint-text">{{ kp }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- 章节时间轴 -->
    <div v-else-if="activeTab === 'chapters'" class="tab-pane">
      <div class="timeline">
        <div
          v-for="(ch, i) in data.chapters" :key="i"
          class="timeline-item"
          :class="{ last: i === data.chapters.length - 1 }"
        >
          <div class="timeline-left">
            <div class="timeline-dot"></div>
            <div v-if="i < data.chapters.length - 1" class="timeline-line"></div>
          </div>
          <div class="timeline-body">
            <div class="timeline-header">
              <span class="timeline-time">{{ ch.time }}</span>
              <span class="timeline-title">{{ ch.title }}</span>
            </div>
            <p class="timeline-content">{{ ch.content }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 思维导图 -->
    <div v-else-if="activeTab === 'mindmap'" class="tab-pane">
      <div class="mindmap-wrapper">
        <div class="mindmap-root">
          <div class="mindmap-center-node">{{ data.mindmap.name }}</div>
          <div class="mindmap-branches">
            <div v-for="(node, ni) in data.mindmap.children" :key="ni" class="mindmap-branch">
              <div class="branch-connector"></div>
              <div class="mindmap-level1">
                <div class="level1-node" :style="{ borderColor: branchColors[ni % branchColors.length] }">
                  {{ node.name }}
                </div>
                <div class="mindmap-leaves">
                  <div
                    v-for="(leaf, li) in node.children" :key="li"
                    class="leaf-node"
                    :style="{ background: branchBgs[ni % branchBgs.length] }"
                  >{{ leaf.name }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 问答 -->
    <div v-else-if="activeTab === 'chat'" class="tab-pane chat-pane">
      <div class="chat-messages" ref="chatBox">
        <div v-if="chatHistory.length === 0" class="chat-empty">
          <div class="chat-empty-icon">🤖</div>
          <p>针对这个视频提问吧</p>
          <p class="chat-empty-hint">回答仅基于视频字幕内容，不会虚构信息</p>
          <div class="chat-suggestions">
            <button v-for="s in suggestions" :key="s" class="suggestion-chip" @click="sendQuestion(s)">{{ s }}</button>
          </div>
        </div>
        <template v-else>
          <div v-for="(msg, i) in chatHistory" :key="i" class="chat-bubble-row" :class="msg.role">
            <div class="chat-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="chat-bubble" :class="msg.role">
              <div class="bubble-content" v-html="formatMsg(msg.content)"></div>
            </div>
          </div>
          <div v-if="chatLoading" class="chat-bubble-row assistant">
            <div class="chat-avatar">🤖</div>
            <div class="chat-bubble assistant">
              <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </template>
      </div>
      <div class="chat-input-row">
        <input
          v-model="chatInput"
          @keyup.enter="sendQuestion(chatInput)"
          :disabled="chatLoading"
          placeholder="输入问题，按回车发送…"
          class="chat-input"
          maxlength="500"
        />
        <button @click="sendQuestion(chatInput)" :disabled="chatLoading || !chatInput.trim()" class="chat-send-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  data: { type: Object, required: true },
  onChat: { type: Function, required: true },
})

const tabs = [
  { id: 'summary',  icon: '📋', label: '概述' },
  { id: 'chapters', icon: '🕐', label: '章节' },
  { id: 'mindmap',  icon: '🧠', label: '思维导图' },
  { id: 'chat',     icon: '💬', label: 'AI 问答' },
]
const activeTab = ref('summary')

const branchColors = ['#ff8c00', '#7c3aed', '#0ea5e9', '#10b981']
const branchBgs = [
  'rgba(255,140,0,0.12)',
  'rgba(124,58,237,0.12)',
  'rgba(14,165,233,0.12)',
  'rgba(16,185,129,0.12)',
]

const chatHistory = ref([])
const chatInput   = ref('')
const chatLoading = ref(false)
const chatBox     = ref(null)

const suggestions = ['这个视频主要讲了什么？', '有哪些核心知识点？', '视频的结论是什么？']

async function sendQuestion(q) {
  q = (q || '').trim()
  if (!q || chatLoading.value) return
  chatInput.value = ''
  chatHistory.value.push({ role: 'user', content: q })
  chatLoading.value = true
  await nextTick()
  scrollChat()
  try {
    const answer = await props.onChat(q, chatHistory.value.slice(0, -1))
    chatHistory.value.push({ role: 'assistant', content: answer })
  } catch (e) {
    chatHistory.value.push({ role: 'assistant', content: '⚠️ ' + (e.message || '请求失败，请重试') })
  } finally {
    chatLoading.value = false
    await nextTick()
    scrollChat()
  }
}

function scrollChat() {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

function formatMsg(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}
</script>

<style scoped>
.ai-summary-panel {
  margin-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.07);
  padding-top: 18px;
  animation: fadeInUp 0.35s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 标签栏 */
.tab-bar {
  display: flex; gap: 6px; margin-bottom: 16px;
  background: rgba(255,255,255,0.04); border-radius: 12px; padding: 4px;
}
.tab-btn {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 5px; padding: 8px 4px; border-radius: 9px; border: none;
  background: transparent; color: rgba(255,255,255,0.45);
  font-size: 0.78rem; font-weight: 500; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
}
.tab-btn:hover { color: rgba(255,255,255,0.75); }
.tab-btn.active {
  background: linear-gradient(135deg,rgba(255,140,0,0.25),rgba(255,69,0,0.15));
  color: #ff8c00; font-weight: 600;
  box-shadow: 0 2px 8px rgba(255,140,0,0.2);
}
.tab-icon { font-size: 0.9rem; }

.tab-pane { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity:0 } to { opacity:1 } }

/* 概述 */
.section-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: 16px;
}
.section-label {
  font-size: 0.7rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: #ff8c00; margin-bottom: 10px;
}
.summary-text { color: rgba(255,255,255,0.82); font-size: 0.9rem; line-height: 1.7; margin: 0; }
.mt-4 { margin-top: 12px; }

/* 要点 */
.keypoints-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.keypoint-item { display: flex; align-items: flex-start; gap: 10px; }
.keypoint-num {
  flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg,#ff8c00,#ff4500);
  color: #fff; font-size: 0.7rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.keypoint-text { color: rgba(255,255,255,0.78); font-size: 0.87rem; line-height: 1.6; padding-top: 2px; }

/* 时间轴 */
.timeline { display: flex; flex-direction: column; }
.timeline-item { display: flex; gap: 12px; }
.timeline-left { display: flex; flex-direction: column; align-items: center; width: 16px; flex-shrink: 0; }
.timeline-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: linear-gradient(135deg,#ff8c00,#ff4500);
  flex-shrink: 0; margin-top: 4px;
  box-shadow: 0 0 8px rgba(255,140,0,0.5);
}
.timeline-line {
  flex: 1; width: 2px;
  background: linear-gradient(to bottom,rgba(255,140,0,0.4),rgba(255,140,0,0.05));
  margin-top: 4px; min-height: 24px;
}
.timeline-body { flex: 1; padding-bottom: 20px; }
.timeline-item.last .timeline-body { padding-bottom: 4px; }
.timeline-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.timeline-time {
  font-size: 0.7rem; font-weight: 700; color: #ff8c00;
  background: rgba(255,140,0,0.12); border: 1px solid rgba(255,140,0,0.25);
  border-radius: 6px; padding: 1px 7px;
  font-family: 'JetBrains Mono', monospace;
}
.timeline-title { color: #fff; font-weight: 600; font-size: 0.88rem; }
.timeline-content { color: rgba(255,255,255,0.5); font-size: 0.82rem; line-height: 1.5; margin: 0; }

/* 思维导图 */
.mindmap-wrapper { overflow-x: auto; padding: 8px 0 4px; }
.mindmap-root { display: flex; flex-direction: column; align-items: center; min-width: 300px; }
.mindmap-center-node {
  background: linear-gradient(135deg,#ff8c00,#ff4500);
  color: #fff; font-weight: 700; font-size: 0.95rem;
  padding: 10px 24px; border-radius: 20px;
  box-shadow: 0 4px 20px rgba(255,140,0,0.4);
  text-align: center; position: relative; z-index: 1;
}
.mindmap-branches {
  display: flex; flex-wrap: wrap; justify-content: center;
  gap: 12px; padding-top: 4px; width: 100%;
}
.mindmap-branch { display: flex; flex-direction: column; align-items: center; }
.branch-connector { width: 2px; height: 20px; background: rgba(255,255,255,0.15); }
.mindmap-level1 { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.level1-node {
  border: 2px solid #ff8c00; background: rgba(255,140,0,0.08);
  color: #fff; font-weight: 600; font-size: 0.82rem;
  padding: 7px 16px; border-radius: 12px;
  text-align: center; min-width: 90px;
}
.mindmap-leaves { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.leaf-node {
  border-radius: 8px; padding: 5px 12px;
  color: rgba(255,255,255,0.72); font-size: 0.78rem;
  text-align: center; min-width: 80px;
  border: 1px solid rgba(255,255,255,0.08);
}

/* AI 问答 */
.chat-pane { display: flex; flex-direction: column; gap: 10px; }
.chat-messages {
  min-height: 200px; max-height: 320px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 12px; padding: 4px 2px;
}
.chat-empty { text-align: center; padding: 24px 0; color: rgba(255,255,255,0.35); font-size: 0.88rem; }
.chat-empty-icon { font-size: 2rem; margin-bottom: 8px; }
.chat-empty-hint { font-size: 0.75rem; color: rgba(255,255,255,0.22); margin-top: 4px; }
.chat-suggestions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 14px; }
.suggestion-chip {
  background: rgba(255,140,0,0.1); border: 1px solid rgba(255,140,0,0.25);
  color: #ff8c00; font-size: 0.78rem; font-weight: 500;
  padding: 5px 12px; border-radius: 99px; cursor: pointer; transition: all 0.2s;
}
.suggestion-chip:hover { background: rgba(255,140,0,0.2); }

.chat-bubble-row { display: flex; gap: 8px; align-items: flex-start; }
.chat-bubble-row.user { flex-direction: row-reverse; }
.chat-avatar { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.chat-bubble { max-width: 82%; padding: 10px 14px; border-radius: 14px; font-size: 0.86rem; line-height: 1.6; }
.chat-bubble.user {
  background: linear-gradient(135deg,rgba(255,140,0,0.25),rgba(255,69,0,0.15));
  border: 1px solid rgba(255,140,0,0.3); color: #fff;
  border-bottom-right-radius: 4px;
}
.chat-bubble.assistant {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.85); border-bottom-left-radius: 4px;
}
.bubble-content :deep(strong) { color: #ff8c00; }

/* 打字动画 */
.typing-dots { display: flex; gap: 4px; align-items: center; padding: 4px 0; }
.typing-dots span {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(255,255,255,0.4);
  animation: bounce 1.2s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* 输入框 */
.chat-input-row { display: flex; gap: 8px; }
.chat-input {
  flex: 1; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
  padding: 10px 14px; color: #e8eaf0; font-size: 0.88rem;
  outline: none; transition: border-color 0.2s;
  font-family: 'Sora', 'Noto Sans SC', sans-serif;
}
.chat-input::placeholder { color: rgba(255,255,255,0.28); }
.chat-input:focus { border-color: rgba(255,140,0,0.5); }
.chat-input:disabled { opacity: 0.5; cursor: not-allowed; }
.chat-send-btn {
  width: 42px; height: 42px; border-radius: 12px; border: none; cursor: pointer;
  background: linear-gradient(135deg,#ff8c00,#ff4500);
  color: #fff; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.2s;
}
.chat-send-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(255,140,0,0.4); }
.chat-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
