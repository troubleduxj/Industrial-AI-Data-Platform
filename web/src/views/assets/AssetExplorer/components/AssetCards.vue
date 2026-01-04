<template>
  <div class="asset-cards-container">
    <n-grid :x-gap="16" :y-gap="16" cols="1 s:2 m:3 l:4 xl:5" responsive="screen">
      <n-grid-item v-for="asset in assets" :key="asset.id">
        <n-card hoverable class="asset-card" @click="handleCardClick(asset)">
          <template #header>
            <div class="card-header">
              <n-icon size="24" :component="getIcon(asset)" :color="getStatusColor(asset.status)" />
              <span class="asset-name text-ellipsis">{{ asset.name }}</span>
            </div>
          </template>
          <template #header-extra>
            <n-tag :type="getStatusType(asset.status)" size="small" round>
              {{ getStatusText(asset.status) }}
            </n-tag>
          </template>
          
          <div class="asset-info">
            <div class="info-row">
              <span class="label">编码:</span>
              <span class="value text-ellipsis">{{ asset.code }}</span>
            </div>
            <div class="info-row">
              <span class="label">位置:</span>
              <span class="value text-ellipsis">{{ asset.location || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">型号:</span>
              <span class="value text-ellipsis">{{ asset.model || '-' }}</span>
            </div>
          </div>
          
          <template #action>
            <n-space justify="end" size="small">
              <n-button size="tiny" secondary type="primary" @click.stop="handleView(asset)">详情</n-button>
              <n-button size="tiny" secondary type="info" @click.stop="handleMonitor(asset)">监控</n-button>
            </n-space>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>
    
    <n-empty v-if="assets.length === 0" description="暂无资产" class="mt-8" />
  </div>
</template>

<script setup>
import { NGrid, NGridItem, NCard, NIcon, NTag, NSpace, NButton, NEmpty } from 'naive-ui'
import { 
  CubeOutline, 
  HardwareChipOutline, 
  ServerOutline,
  DesktopOutline
} from '@vicons/ionicons5'

const props = defineProps({
  assets: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['view', 'monitor'])

function getIcon(asset) {
  // Simple logic to choose icon based on something, defaulting for now
  return CubeOutline
}

function getStatusColor(status) {
  const colors = {
    online: '#18a058',
    offline: '#999',
    error: '#d03050',
    maintenance: '#f0a020'
  }
  return colors[status] || '#999'
}

function getStatusType(status) {
  const types = {
    online: 'success',
    offline: 'default',
    error: 'error',
    maintenance: 'warning'
  }
  return types[status] || 'default'
}

function getStatusText(status) {
  const texts = {
    online: '在线',
    offline: '离线',
    error: '故障',
    maintenance: '维护中'
  }
  return texts[status] || status
}

function handleCardClick(asset) {
  emit('view', asset)
}

function handleView(asset) {
  emit('view', asset)
}

function handleMonitor(asset) {
  emit('monitor', asset)
}
</script>

<style scoped>
.asset-card {
  cursor: pointer;
  transition: all 0.3s;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-name {
  font-weight: 600;
  font-size: 16px;
}

.asset-info {
  font-size: 13px;
  color: var(--n-text-color-3);
}

.info-row {
  display: flex;
  margin-bottom: 4px;
}

.label {
  width: 40px;
  flex-shrink: 0;
}

.value {
  flex: 1;
  color: var(--n-text-color-2);
}

.text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
