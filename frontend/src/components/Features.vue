<template>
  <section id="features" class="py-16 px-4">
    <div class="max-w-5xl mx-auto">
      <h2 class="text-3xl md:text-4xl font-bold text-center mb-3">为什么选择 <span style="color:#ff8c00">VideoSnap</span>？</h2>
      <p class="text-white/40 text-center mb-12">简单、快速、强大——视频下载从未如此容易</p>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div v-for="f in features" :key="f.title" class="glass-card p-6">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-2xl" style="background:linear-gradient(135deg,rgba(255,140,0,0.15),rgba(255,69,0,0.08));border:1px solid rgba(255,140,0,0.2)">{{ f.icon }}</div>
          <h3 class="text-white font-semibold text-lg mb-2">{{ f.title }}</h3>
          <p class="text-white/40 text-sm leading-relaxed">{{ f.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  { icon: '⚡', title: '极速下载', desc: '基于 yt-dlp 强劲内核，解析速度极快，支持多线程并发下载，节省等待时间。' },
  { icon: '🌍', title: '全平台覆盖', desc: '支持 YouTube、B站、抖音、Twitter、Instagram、TikTok 等 1800+ 主流网站。' },
  { icon: '🎬', title: '多种画质', desc: '从 360p 到 4K 超高清任意选择，也支持仅提取音频为 MP3 格式。' },
  { icon: '📱', title: '手机可用', desc: '全响应式设计，手机浏览器直接打开即可使用，无需安装 App。' },
  { icon: '🔒', title: '安全无广告', desc: '无需注册登录，不收集任何个人信息，纯净无广告体验。' },
  { icon: '🆓', title: '完全免费', desc: '核心下载功能永久免费，基于开源项目 yt-dlp 构建，透明可信。' },
]
</script>
