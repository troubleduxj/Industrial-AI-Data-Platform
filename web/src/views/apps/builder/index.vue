<template>
  <div class="app-builder-layout">
    <div class="header">
      <div class="title-area">
        <n-icon size="24" color="#2080f0" class="mr-2">
          <HammerWrench />
        </n-icon>
        <span class="title">App Builder</span>
      </div>
      <div class="actions">
        <n-button size="small" @click="handlePreview">
          <template #icon><n-icon><EyeOutline /></n-icon></template>
          Preview
        </n-button>
        <n-button size="small" type="primary" @click="handleSave">
          <template #icon><n-icon><SaveOutline /></n-icon></template>
          Save App
        </n-button>
      </div>
    </div>
    
    <div class="main-content">
      <div class="left-panel">
        <ComponentLibrary />
      </div>
      <div class="center-panel">
        <Canvas />
      </div>
      <div class="right-panel">
        <PropertyPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent } from 'vue'
import { useMessage } from 'naive-ui'
import { 
  HammerOutline as HammerWrench, 
  EyeOutline,
  SaveOutline
} from '@vicons/ionicons5'
import ComponentLibrary from './components/ComponentLibrary.vue'
import Canvas from './components/Canvas.vue'
import PropertyPanel from './components/PropertyPanel.vue'

defineComponent({
  name: 'AppBuilder'
})

const message = useMessage()

const handlePreview = () => {
  message.info('Preview mode coming soon')
}

const handleSave = () => {
  message.success('App layout saved successfully (Mock)')
}
</script>

<style scoped>
.app-builder-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
}

.header {
  height: 48px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: white;
}

.title-area {
  display: flex;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.mr-2 {
  margin-right: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 200px;
  background: white;
}

.center-panel {
  flex: 1;
  background: #f0f2f5;
  overflow: hidden;
}

.right-panel {
  width: 280px;
  background: white;
}
</style>
