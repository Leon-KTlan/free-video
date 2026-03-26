<template>
  <section id="pricing" class="pricing-section">
    <div class="pricing-header">
      <span class="pricing-badge">透明定价</span>
      <h2 class="pricing-title">选择适合你的套餐</h2>
      <p class="pricing-sub">免费开始，随时升级。无隐藏费用。</p>

      <!-- 月付 / 年付切换 -->
      <div class="billing-toggle">
        <span :class="{ active: billing === 'monthly' }" @click="billing = 'monthly'">月付</span>
        <div class="toggle-track" @click="billing = billing === 'monthly' ? 'yearly' : 'monthly'">
          <div class="toggle-thumb" :class="{ right: billing === 'yearly' }"></div>
        </div>
        <span :class="{ active: billing === 'yearly' }" @click="billing = 'yearly'">
          年付 <em class="save-tag">省 40%</em>
        </span>
      </div>
    </div>

    <div class="plans-grid">
      <div
        v-for="plan in plans"
        :key="plan.id"
        class="plan-card"
        :class="{ featured: plan.id === 'pro', current: userPlan === plan.id }"
      >
        <div v-if="plan.id === 'pro'" class="popular-badge">最受欢迎</div>
        <div v-if="userPlan === plan.id" class="current-badge">当前套餐</div>

        <div class="plan-top">
          <div class="plan-icon">{{ planIcon(plan.id) }}</div>
          <h3 class="plan-name">{{ plan.name }}</h3>

          <div class="plan-price">
            <template v-if="plan.id === 'free'">
              <span class="price-num">¥0</span>
              <span class="price-per">永久免费</span>
            </template>
            <template v-else-if="plan.id === 'annual'">
              <span class="price-num">¥{{ plan.price_yearly }}</span>
              <span class="price-per">/年</span>
              <div class="price-hint">约 ¥{{ (plan.price_yearly / 12).toFixed(1) }}/月</div>
            </template>
            <template v-else>
              <span class="price-num">¥{{ billing === 'monthly' ? plan.price_monthly : plan.price_yearly }}</span>
              <span class="price-per">/{{ billing === 'monthly' ? '月' : '年' }}</span>
              <div v-if="billing === 'yearly'" class="price-hint">约 ¥{{ (plan.price_yearly / 12).toFixed(1) }}/月</div>
            </template>
          </div>
        </div>

        <ul class="feature-list">
          <li v-for="f in plan.features" :key="f" class="feature-item check">
            <span class="icon">✓</span> {{ f }}
          </li>
          <li v-for="l in plan.limits" :key="l" class="feature-item cross">
            <span class="icon">✗</span> {{ l }}
          </li>
        </ul>

        <button
          class="plan-btn"
          :class="plan.id"
          :disabled="userPlan === plan.id || plan.id === 'free'"
          @click="handleUpgrade(plan)"
        >
          {{ btnLabel(plan.id) }}
        </button>
      </div>
    </div>

    <!-- 限制提示弹窗 -->
    <div v-if="showUpgradeModal" class="modal-overlay" @click.self="showUpgradeModal = false">
      <div class="modal-box">
        <button class="modal-close" @click="showUpgradeModal = false">✕</button>
        <div class="modal-icon">⚡</div>
        <h3>{{ upgradeMsg }}</h3>
        <p>升级套餐，享受无限制下载体验</p>
        <button class="modal-cta" @click="scrollToPricing">查看套餐</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  userPlan: { type: String, default: 'free' },
})
const emit = defineEmits(['upgrade'])

const billing = ref('monthly')
const plans = ref([])
const showUpgradeModal = ref(false)
const upgradeMsg = ref('')

onMounted(async () => {
  try {
    const r = await fetch('/api/payment/plans')
    plans.value = await r.json()
  } catch {
    // fallback 静态数据
    plans.value = [
      { id: 'free', name: '免费版', price_monthly: 0, price_yearly: 0,
        daily_downloads: 3, max_quality: 480,
        features: ['每天 3 次下载', '最高 480p 画质', '支持主流平台'],
        limits: ['不支持 1080p/4K', '每天限 3 次'] },
      { id: 'pro', name: '专业版', price_monthly: 18, price_yearly: 128,
        daily_downloads: 100, max_quality: 1080,
        features: ['每天 100 次下载', '最高 1080p 画质', '支持 1800+ 平台', '优先队列', '无广告'],
        limits: [] },
      { id: 'annual', name: '年度旗舰版', price_monthly: null, price_yearly: 198,
        daily_downloads: -1, max_quality: 9999,
        features: ['无限次下载', '最高 4K 画质', '支持 1800+ 平台', '最高优先级', '无广告', '批量下载（即将上线）'],
        limits: [] },
    ]
  }
})

const planIcon = (id) => ({ free: '🌱', pro: '⚡', annual: '👑' }[id] || '📦')

const btnLabel = (id) => {
  if (props.userPlan === id) return '当前套餐'
  if (id === 'free') return '免费使用'
  return '立即升级'
}

const handleUpgrade = (plan) => {
  if (plan.id === 'free' || props.userPlan === plan.id) return
  emit('upgrade', { plan: plan.id, period: plan.id === 'annual' ? 'yearly' : billing.value })
}

const scrollToPricing = () => {
  showUpgradeModal.value = false
  document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })
}

// 暴露给父组件调用
defineExpose({ showLimitModal: (msg) => { upgradeMsg.value = msg; showUpgradeModal.value = true } })
</script>

<style scoped>
.pricing-section {
  padding: 5rem 1.5rem;
  background: #0d0d14;
}
.pricing-header { text-align: center; margin-bottom: 3.5rem; }
.pricing-badge {
  display: inline-block;
  padding: .3rem 1rem;
  border-radius: 99px;
  background: rgba(255,180,0,.12);
  color: #ffb400;
  font-size: .78rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  margin-bottom: 1rem;
}
.pricing-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 4vw, 3rem);
  color: #f0ede8;
  margin: .5rem 0;
}
.pricing-sub { color: #888; font-size: 1.05rem; }

/* 切换 */
.billing-toggle {
  display: inline-flex;
  align-items: center;
  gap: .75rem;
  margin-top: 1.5rem;
  color: #888;
  font-size: .95rem;
  cursor: pointer;
  user-select: none;
}
.billing-toggle span.active { color: #f0ede8; font-weight: 600; }
.save-tag {
  font-style: normal;
  font-size: .72rem;
  background: #ffb400;
  color: #000;
  border-radius: 99px;
  padding: .1rem .5rem;
  margin-left: .3rem;
  font-weight: 700;
}
.toggle-track {
  width: 44px; height: 24px;
  background: #2a2a3a;
  border-radius: 99px;
  position: relative;
  transition: background .2s;
}
.toggle-thumb {
  position: absolute;
  top: 3px; left: 3px;
  width: 18px; height: 18px;
  background: #ffb400;
  border-radius: 50%;
  transition: left .2s;
}
.toggle-thumb.right { left: 23px; }

/* 卡片网格 */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  max-width: 1000px;
  margin: 0 auto;
}
.plan-card {
  position: relative;
  background: #14141f;
  border: 1px solid #2a2a3a;
  border-radius: 1.25rem;
  padding: 2rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: transform .2s, border-color .2s;
}
.plan-card:hover { transform: translateY(-4px); border-color: #3a3a5a; }
.plan-card.featured {
  border-color: #ffb400;
  box-shadow: 0 0 40px rgba(255,180,0,.12);
}
.popular-badge, .current-badge {
  position: absolute;
  top: -13px; left: 50%;
  transform: translateX(-50%);
  background: #ffb400;
  color: #000;
  font-size: .72rem;
  font-weight: 700;
  padding: .25rem .9rem;
  border-radius: 99px;
  white-space: nowrap;
}
.current-badge { background: #4caf50; color: #fff; }

.plan-top { text-align: center; }
.plan-icon { font-size: 2.2rem; margin-bottom: .5rem; }
.plan-name { font-size: 1.2rem; font-weight: 700; color: #f0ede8; margin: 0 0 1rem; }
.plan-price { display: flex; align-items: baseline; justify-content: center; gap: .3rem; flex-wrap: wrap; }
.price-num { font-size: 2.4rem; font-weight: 800; color: #ffb400; line-height: 1; }
.price-per { color: #666; font-size: .95rem; }
.price-hint { width: 100%; text-align: center; font-size: .78rem; color: #666; margin-top: .25rem; }

/* 功能列表 */
.feature-list { list-style: none; margin: 0; padding: 0; flex: 1; display: flex; flex-direction: column; gap: .6rem; }
.feature-item { display: flex; align-items: center; gap: .6rem; font-size: .9rem; }
.feature-item.check { color: #c8c4bc; }
.feature-item.cross { color: #555; }
.feature-item .icon { font-size: .8rem; flex-shrink: 0; }
.feature-item.check .icon { color: #4caf50; }
.feature-item.cross .icon { color: #555; }

/* 按钮 */
.plan-btn {
  width: 100%;
  padding: .85rem;
  border: none;
  border-radius: .75rem;
  font-size: .95rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity .15s, transform .15s;
}
.plan-btn:hover:not(:disabled) { opacity: .85; transform: translateY(-1px); }
.plan-btn:disabled { opacity: .4; cursor: default; transform: none; }
.plan-btn.free { background: #2a2a3a; color: #888; }
.plan-btn.pro { background: #ffb400; color: #000; }
.plan-btn.annual { background: linear-gradient(135deg, #ffb400, #ff6b00); color: #000; }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
}
.modal-box {
  background: #14141f;
  border: 1px solid #ffb400;
  border-radius: 1.25rem;
  padding: 2.5rem 2rem;
  max-width: 360px; width: 90%;
  text-align: center;
  position: relative;
}
.modal-close {
  position: absolute; top: 1rem; right: 1rem;
  background: none; border: none; color: #888;
  font-size: 1.1rem; cursor: pointer;
}
.modal-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.modal-box h3 { color: #f0ede8; font-size: 1.1rem; margin: 0 0 .5rem; }
.modal-box p { color: #888; font-size: .9rem; margin: 0 0 1.5rem; }
.modal-cta {
  background: #ffb400; color: #000;
  border: none; border-radius: .75rem;
  padding: .75rem 2rem; font-weight: 700;
  cursor: pointer; font-size: .95rem;
}
</style>
