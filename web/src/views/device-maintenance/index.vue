<template>
  <div class="device-maintenance-module">
    <CommonPage>
      <div class="module-header">
        <h1 class="module-title">设备维护管理</h1>
        <p class="module-description">
          设备维护模块提供全面的设备维护管理功能，包括维修记录管理、维护计划制定等功能。
        </p>
      </div>

      <div class="module-cards">
        <div class="module-card" @click="navigateToMaintenanceDashboard">
          <div class="card-icon">
            <TheIcon icon="material-symbols:dashboard" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">维护看板</h3>
            <p class="card-description">设备维护状态总览，实时监控设备健康度和维护任务</p>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>

        <div class="module-card" @click="navigateToRepairRecords">
          <div class="card-icon">
            <TheIcon icon="material-symbols:build-circle" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">维修记录</h3>
            <p class="card-description">
              管理设备维修记录，支持故障报修、维修过程跟踪和维修历史查询
            </p>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>

        <!-- 预留其他功能卡片 -->
        <div class="module-card module-card--disabled">
          <div class="card-icon">
            <TheIcon icon="material-symbols:schedule" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">维护计划</h3>
            <p class="card-description">制定和管理设备预防性维护计划（即将推出）</p>
          </div>
          <div class="card-arrow">
            <TheIcon icon="material-symbols:arrow-forward-ios" :size="20" />
          </div>
        </div>

        <div class="module-card module-card--disabled">
          <div class="card-icon">
            <TheIcon icon="material-symbols:analytics" :size="48" />
          </div>
          <div class="card-content">
            <h3 class="card-title">维护统计</h3>
            <p class="card-description">设备维护数据统计分析和报表生成（即将推出）</p>
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

defineOptions({ name: '设备维护管理' })

const router = useRouter()

const navigateToMaintenanceDashboard = () => {
  router.push('/device-maintenance/maintenance-dashboard')
}

const navigateToRepairRecords = () => {
  router.push('/device-maintenance/repair-records')
}
</script>

<style scoped>
.device-maintenance-module {
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
