<template>
  <section class="py-12 px-4">
    <div class="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="s in stats" :key="s.label" class="glass-card p-5 text-center">
        <div class="text-2xl md:text-3xl font-extrabold mb-1" style="background:linear-gradient(135deg,#f7c948,#ff8c00);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{{ s.value }}</div>
        <div class="text-xs text-white/40">{{ s.label }}</div>
      </div>
    </div>
  </section>
</template>

<script setup>
const stats = [
  { value: '1800+', label: '支持网站' },
  { value: '4K', label: '最高画质' },
  { value: '100%', label: '完全免费' },
  { value: '0', label: '需要注册' },
]
</script>
