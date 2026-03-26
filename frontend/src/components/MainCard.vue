<template>
  <div>
    <template v-if="step==='input'">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <input :value="url" @input="$emit('update:url',$event.target.value)"
            @keyup.enter="$emit('fetch')" type="url"
            placeholder="粘贴视频链接，支持 YouTube/B站/抖音/Twitter…"
            class="input-url pr-12" />
          <button v-if="url" @click="$emit('update:url','')"
            class="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <button @click="$emit('fetch')" :disabled="!url.trim()||loading"
          class="btn-primary flex items-center justify-center gap-2" style="min-width:140px">
          <svg v-if="!loading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <svg v-else class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ loading?'解析中…':'解析下载' }}
        </button>
      </div>
      <p v-if="errorMsg" class="mt-4 text-red-400 text-sm flex items-start gap-2">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" class="mt-0.5 flex-shrink-0"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        {{ errorMsg }}
      </p>
      <p class="mt-5 text-xs text-white/25 flex items-center justify-center gap-1.5">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        直接 Ctrl+V / ⌘V 粘贴后按回车
      </p>
    </template>

    <template v-else-if="step==='select'">
      <div class="flex gap-4 mb-6">
        <img v-if="videoInfo.thumbnail" :src="videoInfo.thumbnail"
          class="rounded-xl object-cover flex-shrink-0 bg-white/5"
          style="width:140px;height:88px"
          @error="e=>e.target.style.display='none'" />
        <div v-else class="rounded-xl shimmer flex-shrink-0" style="width:140px;height:88px"></div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-white text-sm md:text-base leading-snug mb-3"
            style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">
            {{ videoInfo.title }}
          </h3>
          <div class="flex flex-wrap gap-2">
            <span v-if="videoInfo.uploader" class="text-xs text-white/45">{{ videoInfo.uploader }}</span>
            <span v-if="videoInfo.duration" class="text-xs text-white/45">{{ fmtDur(videoInfo.duration) }}</span>
            <span v-if="videoInfo.platform" class="text-xs font-semibold px-2 py-0.5 rounded-full"
              style="background:rgba(99,179,237,0.15);color:#63b3ed;border:1px solid rgba(99,179,237,0.25)">
              {{ videoInfo.platform }}
            </span>
          </div>
        </div>
      </div>

      <p class="text-xs font-bold text-white/40 uppercase tracking-widest mb-3">选择下载格式</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-5" style="max-height:260px;overflow-y:auto">
        <div v-for="fmt in videoInfo.formats" :key="fmt.format_id"
          class="format-card cursor-pointer select-none"
          :class="{selected: selectedFormat===fmt.format_id}"
          @click="$emit('update:selected-format',fmt.format_id)">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2.5">
              <div class="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center"
                :style="selectedFormat===fmt.format_id
                  ?'border-color:#ff8c00;background:#ff8c00'
                  :'border-color:rgba(255,255,255,0.2)'">
                <div v-if="selectedFormat===fmt.format_id" class="w-1.5 h-1.5 rounded-full bg-white"></div>
              </div>
              <span class="text-sm font-medium"
                :class="selectedFormat===fmt.format_id?'text-white':'text-white/75'">
                {{ fmt.label }}
              </span>
            </div>
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <span v-if="fmt.size" class="text-xs text-white/35">{{ fmt.size }}</span>
              <span class="text-xs font-bold px-2 py-0.5 rounded-full"
                :style="fmt.type==='audio'
                  ?'background:rgba(154,117,234,0.15);color:#b794f4;border:1px solid rgba(154,117,234,0.25)'
                  :fmt.label.includes('推荐')
                    ?'background:rgba(247,201,72,0.15);color:#f7c948;border:1px solid rgba(247,201,72,0.3)'
                    :'background:rgba(99,179,237,0.12);color:#63b3ed;border:1px solid rgba(99,179,237,0.2)'">
                {{ fmt.ext.toUpperCase() }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="flex gap-3">
        <button @click="$emit('reset')" class="btn-secondary flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg>返回
        </button>
        <button
          @click="$emit('summarize')"
          :disabled="summaryLoading"
          class="btn-secondary flex items-center gap-2"
          style="border-color:rgba(139,92,246,0.4);color:#a78bfa"
        >
          <svg v-if="!summaryLoading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2a7 7 0 0 1 7 7c0 3.5-2.5 6.5-6 7.4V18h-2v-1.6C7.5 15.5 5 12.5 5 9a7 7 0 0 1 7-7z"/><line x1="12" y1="22" x2="12" y2="18"/></svg>
          <svg v-else class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ summaryLoading ? 'AI 分析中…' : 'AI 摘要' }}
        </button>
        <button @click="$emit('start')" :disabled="!selectedFormat"
          class="btn-primary flex-1 flex items-center justify-center gap-2">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          开始下载
        </button>
      </div>

      <!-- AI 摘要错误提示 -->
      <p v-if="summaryError" class="mt-3 text-xs flex items-start gap-1.5" style="color:#f87171">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" class="mt-0.5 flex-shrink-0"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        {{ summaryError }}
      </p>

      <!-- AI 摘要面板（优先用新 VideoSummary 组件） -->
      <VideoSummary
        v-if="summaryData"
        :data="summaryData"
        :on-chat="onChat"
      />
    </template>

    <template v-else-if="step==='downloading'">
      <div class="text-center py-6">
        <div class="w-20 h-20 mx-auto mb-5 rounded-2xl flex items-center justify-center"
          style="background:linear-gradient(135deg,rgba(255,140,0,0.15),rgba(255,69,0,0.08));border:1px solid rgba(255,140,0,0.2)">
          <svg class="animate-spin" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#ff8c00" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
        </div>
        <h3 class="text-white font-bold text-xl mb-2">正在下载…</h3>
        <p class="text-white/40 text-sm mb-7 truncate max-w-xs mx-auto">{{ videoInfo.title }}</p>
        <div class="max-w-sm mx-auto">
          <div class="flex justify-between text-xs text-white/45 mb-2">
            <span>{{ progress.status==='processing'?'后处理中…':(progress.speed||'连接中…') }}</span>
            <span>{{ progress.percent }}%{{ progress.eta?' · 剩余 '+progress.eta:'' }}</span>
          </div>
          <div class="progress-bar"><div class="progress-fill" :style="{width:progress.percent+'%'}"></div></div>
        </div>
      </div>
    </template>

    <template v-else-if="step==='done'">
      <div class="text-center py-6">
        <div class="w-20 h-20 mx-auto mb-5 rounded-2xl flex items-center justify-center"
          style="background:linear-gradient(135deg,rgba(52,211,153,0.15),rgba(16,185,129,0.08));border:1px solid rgba(52,211,153,0.3)">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <h3 class="text-white font-bold text-xl mb-2">下载完成！</h3>
        <p class="text-white/40 text-sm mb-7">视频已准备好，点击保存到本地</p>
        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <a :href="downloadUrl" :download="downloadFilename"
            class="btn-primary flex items-center justify-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            保存文件
          </a>
          <button @click="$emit('reset')" class="btn-secondary flex items-center justify-center gap-2">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3"/></svg>
            继续下载
          </button>
        </div>
      </div>
    </template>

    <template v-else-if="step==='error'">
      <div class="text-center py-6">
        <div class="w-20 h-20 mx-auto mb-5 rounded-2xl flex items-center justify-center"
          style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3)">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <h3 class="text-white font-bold text-xl mb-2">下载失败</h3>
        <p class="text-red-400/80 text-sm mb-7 max-w-sm mx-auto">{{ errorMsg }}</p>
        <button @click="$emit('reset')" class="btn-secondary">重新尝试</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.sessdata-block {
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px;
  overflow: hidden;
}
.sessdata-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: .76rem;
  color: rgba(255,255,255,.4);
  cursor: pointer;
  list-style: none;
  user-select: none;
}
.sessdata-summary:hover { color: rgba(255,255,255,.65); }
.sessdata-body {
  padding: 8px 12px 12px;
  border-top: 1px solid rgba(255,255,255,.06);
}
.sessdata-tip {
  font-size: .73rem;
  color: rgba(255,255,255,.3);
  margin-bottom: 8px;
  line-height: 1.5;
}
.sessdata-tip code {
  background: rgba(255,140,0,.15);
  color: #ff8c00;
  padding: 1px 5px;
  border-radius: 4px;
  font-family: monospace;
}
.sessdata-input {
  width: 100%;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  padding: 7px 11px;
  color: #e8eaf0;
  font-size: .82rem;
  outline: none;
  transition: border-color .2s;
  box-sizing: border-box;
}
.sessdata-input::placeholder { color: rgba(255,255,255,.2); }
.sessdata-input:focus { border-color: rgba(255,140,0,.5); }
</style>

<script setup>
import VideoSummary from './VideoSummary.vue'
import AISummaryPanel from './AISummary.vue'

defineProps({
  step: String, url: String, loading: Boolean, errorMsg: String,
  videoInfo: Object, selectedFormat: String,
  progress: Object, downloadUrl: String, downloadFilename: String,
  summaryLoading: { type: Boolean, default: false },
  summaryError: { type: String, default: '' },
  summaryData: { type: Object, default: null },
  onChat: { type: Function, default: null },
})
defineEmits(['update:url','fetch','update:selected-format','start','reset','summarize'])

function fmtDur(s) {
  if (!s) return ''
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60
  return h
    ? `${h}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
    : `${m}:${String(sec).padStart(2,'0')}`
}
</script>
