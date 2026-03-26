<template>
  <div class="vs-panel">
    <div class="vs-tabs">
      <button v-for="tab in tabs" :key="tab.id"
        class="vs-tab" :class="{active: activeTab===tab.id}"
        @click="activeTab=tab.id"
      ><span>{{ tab.icon }}</span><span>{{ tab.label }}</span></button>
    </div>

    <!-- 总结 -->
    <div v-if="activeTab==='summary'" class="vs-pane">
      <div class="vs-card">
        <div class="vs-label">核心概述</div>
        <p class="vs-summary-text">{{ data.summary }}</p>
      </div>
      <div class="vs-card" style="margin-top:12px">
        <div class="vs-label">核心要点</div>
        <ul class="vs-kp-list">
          <li v-for="(kp,i) in data.keypoints" :key="i" class="vs-kp-item">
            <span class="vs-kp-num">{{ i+1 }}</span>
            <span>{{ kp }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- 字幕 -->
    <div v-else-if="activeTab==='transcript'" class="vs-pane">
      <div class="vs-transcript-box">
        <p class="vs-transcript-text">{{ data.transcript || '暂无字幕文本' }}</p>
      </div>
    </div>

    <!-- 导图 -->
    <div v-else-if="activeTab==='mindmap'" class="vs-pane">
      <div class="vs-mindmap">
        <div class="vs-mm-center">{{ data.mindmap.name }}</div>
        <div class="vs-mm-branches">
          <div v-for="(node,ni) in data.mindmap.children" :key="ni" class="vs-mm-branch">
            <div class="vs-mm-connector"></div>
            <div class="vs-mm-l1" :style="{borderColor:colors[ni%colors.length]}">{{ node.name }}</div>
            <div class="vs-mm-leaves">
              <div v-for="(leaf,li) in node.children" :key="li"
                class="vs-mm-leaf" :style="{background:colorBgs[ni%colorBgs.length]}"
              >{{ leaf.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 问答 -->
    <div v-else-if="activeTab==='chat'" class="vs-pane vs-chat-pane">
      <div class="vs-chat-msgs" ref="chatEl">
        <div v-if="!chatHistory.length" class="vs-chat-empty">
          <div style="font-size:2rem;margin-bottom:8px">🤖</div>
          <p>针对这个视频提问吧</p>
          <p style="font-size:.75rem;color:rgba(255,255,255,.22);margin-top:4px">回答仅基于视频字幕内容</p>
          <div class="vs-suggestions">
            <button v-for="s in suggestions" :key="s" class="vs-chip" @click="send(s)">{{ s }}</button>
          </div>
        </div>
        <template v-else>
          <div v-for="(m,i) in chatHistory" :key="i" class="vs-bubble-row" :class="m.role">
            <div class="vs-avatar">{{ m.role==='user'?'👤':'🤖' }}</div>
            <div class="vs-bubble" :class="m.role" v-html="fmt(m.content)"></div>
          </div>
          <div v-if="chatLoading" class="vs-bubble-row assistant">
            <div class="vs-avatar">🤖</div>
            <div class="vs-bubble assistant"><div class="vs-dots"><span></span><span></span><span></span></div></div>
          </div>
        </template>
      </div>
      <div class="vs-input-row">
        <input v-model="chatInput" @keyup.enter="send(chatInput)" :disabled="chatLoading"
          placeholder="输入问题，按回车发送…" class="vs-input" maxlength="500"/>
        <button @click="send(chatInput)" :disabled="chatLoading||!chatInput.trim()" class="vs-send-btn">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
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
  { id:'summary',    icon:'📋', label:'总结' },
  { id:'transcript', icon:'📝', label:'字幕' },
  { id:'mindmap',    icon:'🧠', label:'导图' },
  { id:'chat',       icon:'💬', label:'问答' },
]
const activeTab   = ref('summary')
const chatHistory = ref([])
const chatInput   = ref('')
const chatLoading = ref(false)
const chatEl      = ref(null)
const colors    = ['#ff8c00','#7c3aed','#0ea5e9','#10b981']
const colorBgs  = ['rgba(255,140,0,.12)','rgba(124,58,237,.12)','rgba(14,165,233,.12)','rgba(16,185,129,.12)']
const suggestions = ['这个视频主要讲了什么？','有哪些核心知识点？','视频的结论是什么？']
async function send(q) {
  q=(q||'').trim()
  if(!q||chatLoading.value) return
  chatInput.value=''
  chatHistory.value.push({role:'user',content:q})
  chatLoading.value=true
  await nextTick(); scroll()
  try {
    const ans = await props.onChat(q, chatHistory.value.slice(0,-1))
    chatHistory.value.push({role:'assistant',content:ans})
  } catch(e) {
    chatHistory.value.push({role:'assistant',content:'⚠️ '+(e.message||'请求失败')})
  } finally {
    chatLoading.value=false
    await nextTick(); scroll()
  }
}
function scroll(){ if(chatEl.value) chatEl.value.scrollTop=chatEl.value.scrollHeight }
function fmt(t){
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\n/g,'<br/>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
}
</script>

<style scoped>
.vs-panel{margin-top:20px;border-top:1px solid rgba(255,255,255,.07);padding-top:18px;animation:vsFadeUp .35s ease}
@keyframes vsFadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

/* 标签栏 */
.vs-tabs{display:flex;gap:5px;margin-bottom:14px;background:rgba(255,255,255,.04);border-radius:12px;padding:4px}
.vs-tab{flex:1;display:flex;align-items:center;justify-content:center;gap:5px;padding:7px 4px;border-radius:9px;border:none;background:transparent;color:rgba(255,255,255,.4);font-size:.77rem;font-weight:500;cursor:pointer;transition:all .2s;white-space:nowrap}
.vs-tab:hover{color:rgba(255,255,255,.75)}
.vs-tab.active{background:linear-gradient(135deg,rgba(255,140,0,.25),rgba(255,69,0,.15));color:#ff8c00;font-weight:600;box-shadow:0 2px 8px rgba(255,140,0,.2)}
.vs-pane{animation:vsFadeIn .2s ease}
@keyframes vsFadeIn{from{opacity:0}to{opacity:1}}

/* 卡片 */
.vs-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:14px}
.vs-label{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#ff8c00;margin-bottom:8px}
.vs-summary-text{color:rgba(255,255,255,.82);font-size:.88rem;line-height:1.7;margin:0}

/* 要点 */
.vs-kp-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:7px}
.vs-kp-item{display:flex;align-items:flex-start;gap:9px;color:rgba(255,255,255,.78);font-size:.85rem;line-height:1.6}
.vs-kp-num{flex-shrink:0;width:20px;height:20px;border-radius:50%;background:linear-gradient(135deg,#ff8c00,#ff4500);color:#fff;font-size:.68rem;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:1px}

/* 字幕 */
.vs-transcript-box{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:14px;max-height:300px;overflow-y:auto}
.vs-transcript-text{color:rgba(255,255,255,.6);font-size:.82rem;line-height:1.8;margin:0;white-space:pre-wrap;word-break:break-all}

/* 导图 */
.vs-mindmap{overflow-x:auto;padding:8px 0 4px;display:flex;flex-direction:column;align-items:center}
.vs-mm-center{background:linear-gradient(135deg,#ff8c00,#ff4500);color:#fff;font-weight:700;font-size:.9rem;padding:9px 22px;border-radius:20px;box-shadow:0 4px 18px rgba(255,140,0,.4);text-align:center;margin-bottom:0}
.vs-mm-branches{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;padding-top:4px;width:100%}
.vs-mm-branch{display:flex;flex-direction:column;align-items:center}
.vs-mm-connector{width:2px;height:18px;background:rgba(255,255,255,.15)}
.vs-mm-l1{border:2px solid #ff8c00;background:rgba(255,140,0,.08);color:#fff;font-weight:600;font-size:.8rem;padding:6px 14px;border-radius:11px;text-align:center;min-width:80px}
.vs-mm-leaves{display:flex;flex-direction:column;gap:4px;align-items:center;margin-top:6px}
.vs-mm-leaf{border-radius:8px;padding:4px 10px;color:rgba(255,255,255,.7);font-size:.76rem;text-align:center;min-width:70px;border:1px solid rgba(255,255,255,.08)}

/* 问答 */
.vs-chat-pane{display:flex;flex-direction:column;gap:8px}
.vs-chat-msgs{min-height:180px;max-height:300px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding:2px}
.vs-chat-empty{text-align:center;padding:20px 0;color:rgba(255,255,255,.35);font-size:.86rem}
.vs-suggestions{display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:12px}
.vs-chip{background:rgba(255,140,0,.1);border:1px solid rgba(255,140,0,.25);color:#ff8c00;font-size:.76rem;padding:4px 11px;border-radius:99px;cursor:pointer;transition:all .2s}
.vs-chip:hover{background:rgba(255,140,0,.2)}
.vs-bubble-row{display:flex;gap:7px;align-items:flex-start}
.vs-bubble-row.user{flex-direction:row-reverse}
.vs-avatar{font-size:1rem;flex-shrink:0;margin-top:2px}
.vs-bubble{max-width:82%;padding:9px 13px;border-radius:13px;font-size:.84rem;line-height:1.6}
.vs-bubble.user{background:linear-gradient(135deg,rgba(255,140,0,.25),rgba(255,69,0,.15));border:1px solid rgba(255,140,0,.3);color:#fff;border-bottom-right-radius:4px}
.vs-bubble.assistant{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);color:rgba(255,255,255,.85);border-bottom-left-radius:4px}
.vs-bubble :deep(strong){color:#ff8c00}
.vs-dots{display:flex;gap:4px;align-items:center;padding:4px 0}
.vs-dots span{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.4);animation:vsBounce 1.2s infinite ease-in-out}
.vs-dots span:nth-child(2){animation-delay:.2s}
.vs-dots span:nth-child(3){animation-delay:.4s}
@keyframes vsBounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
.vs-input-row{display:flex;gap:7px}
.vs-input{flex:1;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:11px;padding:9px 13px;color:#e8eaf0;font-size:.86rem;outline:none;transition:border-color .2s;font-family:'Sora','Noto Sans SC',sans-serif}
.vs-input::placeholder{color:rgba(255,255,255,.28)}
.vs-input:focus{border-color:rgba(255,140,0,.5)}
.vs-input:disabled{opacity:.5;cursor:not-allowed}
.vs-send-btn{width:40px;height:40px;border-radius:11px;border:none;cursor:pointer;background:linear-gradient(135deg,#ff8c00,#ff4500);color:#fff;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s}
.vs-send-btn:hover:not(:disabled){transform:translateY(-1px);box-shadow:0 4px 14px rgba(255,140,0,.4)}
.vs-send-btn:disabled{opacity:.4;cursor:not-allowed}
</style>
