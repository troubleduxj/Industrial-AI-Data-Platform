<template>
  <div class="device-module">
    <CommonPage>
      <div class="module-header">
        <h1 class="module-title">设备管理</h1>
        <p class="module-description">
          设备管理模块提供设备信息管理、设备分类管理等功能，帮助您全面管理设备资产。
        </p>
      </div>

      <div class="module-cards">
        <div class="module-card" @click="navigateToBaseinfo">
          <div class="card-icon">
            <TheIcon icon="material-symbols:info" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">设备信息管理</h3>
            <p class="card-description">管理设备基本信息，包括设备档案、参数配置等</p>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>

        <div class="module-card" @click="navigateToType">
          <div class="card-icon">
            <TheIcon icon="material-symbols:category" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">设备分类管理</h3>
            <p class="card-description">管理设备类型和分类，定义设备属性模板</p>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>
      </div>
    </CommonPage>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

defineOptions({ name: '设备管理' })

const router = useRouter()

const navigateToBaseinfo = () => {
  router.push('/device/baseinfo')
}

const navigateToType = () => {
  router.push('/device/type')
}
</script>

<style scoped>
.device-module {
  padding: 20px;
}

.module-header {
  text-align: center;
  margin-bottom: 40px;
}

.module-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 12px 0;
}

.module-description {
  font-size: 16px;
  color: var(--n-text-color-2);
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.module-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.module-card {
  display: flex;
  align-items: center;
  padding: 24px;
  background: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px var(--n-box-shadow-color);
  border-color: var(--n-primary-color);
}

.module-card--disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.module-card--disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--n-border-color);
}

.card-icon {
  flex-shrink: 0;
  margin-right: 20px;
  color: var(--n-primary-color);
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-title-text-color);
  margin: 0 0 8px 0;
}

.card-description {
  font-size: 14px;
  color: var(--n-text-color-2);
  margin: 0;
  line-height: 1.5;
}

.card-arrow {
  flex-shrink: 0;
  margin-left: 16px;
  color: var(--n-text-color-3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .module-cards {
    grid-template-columns: 1fr;
  }

  .module-card {
    padding: 20px;
  }

  .card-icon {
    margin-right: 16px;
  }
}
</style>
