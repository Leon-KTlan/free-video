<template>
  <section id="platforms" class="py-16 px-4">
    <div class="max-w-4xl mx-auto text-center">
      <h2 class="text-3xl font-bold mb-3">支持的平台</h2>
      <p class="text-white/40 mb-10">以下仅为部分展示，实际支持 1800+ 网站</p>
      <div class="flex flex-wrap justify-center gap-3">
        <div v-for="p in platforms" :key="p.name"
          class="glass-card px-5 py-3 flex items-center gap-2 text-sm font-medium text-white/70 hover:text-white transition-colors cursor-default">
          <span class="text-lg">{{ p.icon }}</span>
          {{ p.name }}
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const platforms = [
  { name: 'YouTube', icon: '▶️' },
  { name: 'B站', icon: '📺' },
  { name: '抖音', icon: '🎵' },
  { name: 'Twitter/X', icon: '🐦' },
  { name: 'Instagram', icon: '📷' },
  { name: 'TikTok', icon: '🎬' },
  { name: 'Facebook', icon: '👥' },
  { name: 'Vimeo', icon: '🎞️' },
  { name: '微博', icon: '🌐' },
  { name: '西瓜视频', icon: '🍉' },
  { name: '腾讯视频', icon: '🐧' },
  { name: '优酷', icon: '🦊' },
  { name: 'Reddit', icon: '🤖' },
  { name: 'Twitch', icon: '🎮' },
  { name: '1800+ 更多…', icon: '✨' },
]
</script>
