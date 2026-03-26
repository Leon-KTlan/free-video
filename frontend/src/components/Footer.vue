<template>
  <footer id="faq" class="py-16 px-4 border-t" style="border-color:rgba(255,255,255,0.06)">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-2xl font-bold text-center mb-10">常见问题</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-16">
        <div v-for="q in faqs" :key="q.q" class="glass-card p-5">
          <h4 class="text-white font-semibold mb-2 flex items-start gap-2">
            <span style="color:#ff8c00" class="flex-shrink-0 mr-1">Q</span>{{ q.q }}
          </h4>
          <p class="text-white/45 text-sm leading-relaxed">{{ q.a }}</p>
        </div>
      </div>
      <div class="text-center text-white/25 text-sm">
        <p class="mb-2"><span style="color:#ff8c00;font-weight:700">VideoSnap</span> — 基于开源项目 yt-dlp 构建</p>
        <p>请尊重版权，仅供个人学习使用。</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
const faqs = [
  { q: '支持哪些网站？', a: '基于 yt-dlp，支持 YouTube、B站、抖音、Twitter/X、Instagram、TikTok、Facebook、Vimeo 等 1800+ 网站。' },
  { q: '下载的视频画质如何？', a: '支持从 360p 到 4K 超高清的全部可用画质，选择「最佳画质」即可自动获取最高分辨率。' },
  { q: '手机上能用吗？', a: '完全支持！使用手机浏览器打开网站，操作方式与电脑完全一致，响应式设计自动适配。' },
  { q: '下载需要登录吗？', a: '无需注册或登录，直接粘贴视频链接即可使用，完全匿名。' },
  { q: '下载速度慢怎么办？', a: '下载速度取决于服务器网络和视频源平台的限速。选择较低画质可以加快速度。' },
  { q: '版权声明', a: '本工具仅供学习研究使用，请遵守所在地区法律法规，尊重内容创作者版权，勿用于商业用途。' },
]
</script>
