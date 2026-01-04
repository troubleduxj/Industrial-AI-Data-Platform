<template>
  <div class="canvas-container" @click.self="selectComponent(null)">
    <div v-if="components.length === 0" class="empty-state">
      <div class="empty-content">
        <n-icon size="48" color="#ccc"><ConstructOutline /></n-icon>
        <p>Click a component on the left to add it.</p>
      </div>
    </div>
    <div 
      v-for="comp in components" 
      :key="comp.id"
      class="canvas-item"
      :class="{ selected: selectedId === comp.id }"
      @click.stop="selectComponent(comp.id)"
    >
      <div class="item-actions" v-if="selectedId === comp.id">
        <n-button size="tiny" type="error" circle @click.stop="removeComponent(comp.id)">
          <template #icon><n-icon><TrashOutline /></n-icon></template>
        </n-button>
      </div>
      
      <!-- Render Components -->
      <n-card v-if="comp.type === 'container'" :title="comp.props.title" :bordered="comp.props.bordered" style="margin-bottom: 0;">
        <div class="container-placeholder">Container Content (Drop here coming soon)</div>
      </n-card>

      <n-button v-else-if="comp.type === 'button'" :type="comp.props.type">
        {{ comp.props.content }}
      </n-button>

      <div v-else-if="comp.type === 'text'" :style="{ fontSize: comp.props.fontSize + 'px', fontWeight: comp.props.fontWeight }">
        {{ comp.props.content }}
      </div>

      <n-input v-else-if="comp.type === 'input'" :placeholder="comp.props.placeholder" />

      <n-statistic v-else-if="comp.type === 'statistic'" :label="comp.props.label">
        <template #prefix>{{ comp.props.prefix }}</template>
        <template #suffix>{{ comp.props.suffix }}</template>
        {{ comp.props.value }}
      </n-statistic>

      <div v-else-if="comp.type === 'chart'" :style="{ height: comp.props.height + 'px' }" class="chart-placeholder">
        <n-icon size="32" color="#ccc"><StatsChartOutline /></n-icon>
        <span>Chart: {{ comp.props.title }} ({{ comp.props.type }})</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useBuilder } from '../useBuilder'
import { TrashOutline, ConstructOutline, StatsChartOutline } from '@vicons/ionicons5'

const { components, selectedId, selectComponent, removeComponent } = useBuilder()
</script>

<style scoped>
.canvas-container {
  padding: 24px;
  height: 100%;
  background-color: #f0f2f5;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}
.empty-content {
  text-align: center;
}
.canvas-item {
  position: relative;
  border: 2px solid transparent;
  padding: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.canvas-item:hover {
  border-color: #e6f7ff;
}
.canvas-item.selected {
  border-color: #1890ff;
  border-style: dashed;
}
.item-actions {
  position: absolute;
  top: -12px;
  right: -12px;
  z-index: 10;
}
.chart-placeholder {
  background: white;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: center;
  border: 1px solid #eee;
  border-radius: 4px;
  color: #666;
}
.container-placeholder {
  padding: 20px;
  text-align: center;
  color: #ccc;
  border: 1px dashed #eee;
  background: #fafafa;
}
</style>
