<template>
  <div class="property-panel">
    <div class="section-title">Properties</div>
    <div v-if="selectedComponent">
      <n-form label-placement="top" size="small">
        <n-form-item label="ID">
          <n-input :value="selectedComponent.id" disabled placeholder="Component ID" />
        </n-form-item>
        <n-form-item label="Type">
          <n-tag type="info">{{ selectedComponent.type }}</n-tag>
        </n-form-item>
        
        <n-divider />

        <!-- Dynamic Props -->
        <template v-for="(val, key) in selectedComponent.props" :key="key">
          <n-form-item :label="formatLabel(key)">
             <n-switch v-if="typeof val === 'boolean'" :value="val" @update:value="(v) => updateProps(selectedComponent!.id, { [key]: v })" />
             <n-input-number v-else-if="typeof val === 'number'" :value="val" @update:value="(v) => updateProps(selectedComponent!.id, { [key]: v })" style="width: 100%" />
             <n-input v-else :value="val" @update:value="(v) => updateProps(selectedComponent!.id, { [key]: v })" />
          </n-form-item>
        </template>
      </n-form>
    </div>
    <div v-else class="empty-state">
      <n-empty description="Select a component to edit properties" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useBuilder } from '../useBuilder'

const { selectedComponent, updateProps } = useBuilder()

const formatLabel = (key: string) => {
  return key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1').trim()
}
</script>

<style scoped>
.property-panel {
  padding: 16px;
  border-left: 1px solid #eee;
  height: 100%;
  overflow-y: auto;
}
.section-title {
  font-weight: bold;
  margin-bottom: 16px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}
</style>
