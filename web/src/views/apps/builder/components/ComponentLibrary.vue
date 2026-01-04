<template>
  <div class="component-library">
    <div class="section-title">Components</div>
    <div class="component-list">
      <div 
        v-for="item in availableComponents" 
        :key="item.type" 
        class="component-item"
        @click="addComponent(item.type)"
      >
        <n-icon size="20">
          <component :is="item.icon" />
        </n-icon>
        <span>{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useBuilder } from '../useBuilder'
import { 
  SquareOutline, 
  ReaderOutline, 
  CreateOutline, 
  StatsChartOutline, 
  AlbumsOutline,
  CodeWorkingOutline
} from '@vicons/ionicons5'

const { addComponent } = useBuilder()

const availableComponents = [
  { type: 'container', label: 'Container', icon: SquareOutline },
  { type: 'button', label: 'Button', icon: CodeWorkingOutline },
  { type: 'text', label: 'Text', icon: ReaderOutline },
  { type: 'input', label: 'Input', icon: CreateOutline },
  { type: 'statistic', label: 'Statistic', icon: AlbumsOutline },
  { type: 'chart', label: 'Chart', icon: StatsChartOutline },
] as const
</script>

<style scoped>
.component-library {
  padding: 16px;
  border-right: 1px solid #eee;
  height: 100%;
}
.section-title {
  font-weight: bold;
  margin-bottom: 12px;
  color: #666;
}
.component-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}
.component-item:hover {
  background-color: #f5f5f5;
  border-color: #d9d9d9;
  color: #1890ff;
}
</style>
