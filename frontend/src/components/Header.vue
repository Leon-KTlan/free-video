<template>
  <header class="flex items-center justify-between px-6 md:px-12 py-5">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-xl flex items-center justify-center" style="background:linear-gradient(135deg,#ff8c00,#ff4500)">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M5 3l14 9-14 9V3z" fill="white"/></svg>
      </div>
      <span class="text-xl font-bold tracking-tight" style="background:linear-gradient(135deg,#fff 0%,#ff8c00 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent">VideoSnap</span>
    </div>
    <nav class="hidden md:flex items-center gap-6 text-sm text-white/50">
      <a href="#features" class="hover:text-white/80 transition-colors">功能介绍</a>
      <a href="#platforms" class="hover:text-white/80 transition-colors">支持平台</a>
      <a href="#faq" class="hover:text-white/80 transition-colors">常见问题</a>
    </nav>
    <span class="hidden md:inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full" style="background:rgba(247,201,72,0.12);color:#f7c948;border:1px solid rgba(247,201,72,0.2)">
      <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>服务正常
    </span>
  </header>
</template>
