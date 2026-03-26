<template>
  <div class="min-h-screen relative overflow-x-hidden">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    <div class="fixed inset-0 z-0 pointer-events-none" style="background-image:linear-gradient(rgba(255,255,255,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.025) 1px,transparent 1px);background-size:60px 60px"></div>
    <div class="relative z-10">
      <AppHeader />
      <main class="px-4 pt-16 pb-8 md:pt-24">
        <!-- Hero -->
        <div class="text-center mb-10">
          <div class="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-full mb-8" style="background:rgba(255,140,0,0.1);color:#ff8c00;border:1px solid rgba(255,140,0,0.25)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            支持 1800+ 网站 · 免费使用 · 无需登录
          </div>
          <h1 class="text-4xl md:text-6xl font-extrabold leading-tight mb-5 tracking-tight">
            <span class="text-white">一键下载</span><br/>
            <span style="background:linear-gradient(135deg,#f7c948 0%,#ff8c00 50%,#ff4500 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent">任意平台视频</span>
          </h1>
          <p class="text-white/50 text-lg max-w-2xl mx-auto leading-relaxed">YouTube、B站、抖音、Twitter、Instagram… 粘贴链接，立即下载</p>
        </div>

        <!-- Main card -->
        <div class="glass-card max-w-3xl mx-auto p-6 md:p-8">
          <MainCard
            :step="step" :url="url" :loading="loading" :error-msg="errorMsg"
            :video-info="videoInfo" :selected-format="selectedFormat"
            :progress="progress" :download-url="downloadUrl" :download-filename="downloadFilename"
            @update:url="url=$event"
            @fetch="fetchInfo"
            @update:selected-format="selectedFormat=$event"
            @start="startDownload"
            @reset="reset"
          />
        </div>
      </main>
      <Stats />
      <Features />
      <Platforms />
      <AppFooter />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import AppHeader from './components/Header.vue'
import MainCard from './components/MainCard.vue'
import Stats from './components/Stats.vue'
import Features from './components/Features.vue'
import Platforms from './components/Platforms.vue'
import AppFooter from './components/Footer.vue'

const url = ref('')
const loading = ref(false)
const step = ref('input')
const videoInfo = reactive({ title:'', thumbnail:'', duration:0, uploader:'', platform:'', formats:[] })
const selectedFormat = ref('')
const progress = reactive({ status:'', percent:0, speed:'', eta:'' })
const downloadUrl = ref('')
const downloadFilename = ref('')
const errorMsg = ref('')
let taskId = ''

async function fetchInfo() {
  if (!url.value.trim()) return
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await axios.post('/api/info', { url: url.value.trim() })
    Object.assign(videoInfo, res.data)
    selectedFormat.value = res.data.formats?.[0]?.format_id || 'best'
    step.value = 'select'
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '解析失败，请检查链接是否正确'
  } finally {
    loading.value = false
  }
}

async function startDownload() {
  if (!selectedFormat.value) return
  taskId = Date.now().toString(36) + Math.random().toString(36).slice(2)
  step.value = 'downloading'
  Object.assign(progress, { status:'downloading', percent:0, speed:'', eta:'' })
  try {
    await axios.post('/api/download', { url: url.value.trim(), format_id: selectedFormat.value, task_id: taskId })
    const es = new EventSource(`/api/progress/${taskId}`)
    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      Object.assign(progress, data)
      if (data.status === 'done') {
        es.close()
        downloadUrl.value = data.download_url
        downloadFilename.value = data.filename || 'video.mp4'
        step.value = 'done'
      } else if (data.status === 'error') {
        es.close()
        errorMsg.value = data.error || '下载失败'
        step.value = 'error'
      }
    }
    es.onerror = () => { es.close(); errorMsg.value = '连接中断，请重试'; step.value = 'error' }
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '启动下载失败'
    step.value = 'error'
  }
}

function reset() {
  step.value = 'input'
  url.value = ''
  errorMsg.value = ''
  selectedFormat.value = ''
  Object.assign(progress, { status:'', percent:0, speed:'', eta:'' })
  downloadUrl.value = ''
  downloadFilename.value = ''
  Object.assign(videoInfo, { title:'', thumbnail:'', duration:0, uploader:'', platform:'', formats:[] })
}
</script>
