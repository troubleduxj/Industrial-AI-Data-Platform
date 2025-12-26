<template>
  <div class="ai-config-editor">
    <n-card size="small" title="AI 分析配置">
      <n-grid :cols="2" :x-gap="12">
        <n-form-item-grid-item label="算法模型">
          <n-select
            v-model:value="config.algorithm"
            :options="algorithmOptions"
            placeholder="选择算法"
          />
        </n-form-item-grid-item>

        <n-form-item-grid-item label="数据归一化">
          <n-select
            v-model:value="config.normalization"
            :options="normalizationOptions"
            placeholder="选择归一化方式"
          />
        </n-form-item-grid-item>
      </n-grid>

      <n-grid :cols="2" :x-gap="12">
        <n-form-item-grid-item label="时间窗口大小">
          <n-input-number
            v-model:value="config.window_size"
            :min="1"
            placeholder="例如: 100"
            style="width: 100%"
          />
        </n-form-item-grid-item>

        <n-form-item-grid-item label="异常阈值 (可选)">
          <n-input-number
            v-model:value="config.threshold"
            :min="0"
            :step="0.01"
            placeholder="例如: 0.95"
            style="width: 100%"
          />
        </n-form-item-grid-item>
      </n-grid>

      <n-form-item label="特征字段选择" :show-label="true">
        <n-transfer
          v-model:value="config.features"
          :options="fieldOptions"
          source-title="可选字段"
          target-title="特征字段"
          filterable
        />
      </n-form-item>
    </n-card>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { NCard, NGrid, NFormItemGridItem, NSelect, NInputNumber, NFormItem, NTransfer } from 'naive-ui'

const props = defineProps({
  value: {
    type: Object,
    default: () => ({})
  },
  fields: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:value'])

// 默认配置
const defaultConfig = {
  algorithm: 'isolation_forest',
  normalization: 'min-max',
  window_size: 100,
  features: [],
  threshold: null
}

// 内部响应式状态
const config = ref({ ...defaultConfig, ...(props.value || {}) })

// 算法选项
const algorithmOptions = [
  { label: '孤立森林 (Isolation Forest)', value: 'isolation_forest' },
  { label: 'LSTM 预测', value: 'lstm' },
  { label: 'SVM 分类', value: 'svm' },
  { label: 'DBSCAN 聚类', value: 'dbscan' }
]

// 归一化选项
const normalizationOptions = [
  { label: 'Min-Max 归一化', value: 'min-max' },
  { label: 'Z-Score 标准化', value: 'z-score' },
  { label: '不处理', value: 'none' }
]

// 字段选项
const fieldOptions = computed(() => {
  return props.fields.map(f => ({
    label: f.label || f,
    value: f.value || f
  }))
})

// 监听 config 变化并向上发射
watch(config, (newVal) => {
  emit('update:value', newVal)
}, { deep: true })

// 监听 props.value 变化
watch(() => props.value, (newVal) => {
  if (newVal) {
    const merged = { ...defaultConfig, ...newVal }
    if (JSON.stringify(merged) !== JSON.stringify(config.value)) {
      config.value = merged
    }
  }
}, { deep: true })

</script>

<style scoped>
.ai-config-editor {
  margin-top: 10px;
}
</style>
