<template>
  <div class="aggregation-config-editor">
    <n-card size="small" title="聚合配置">
      <n-grid :cols="2" :x-gap="12">
        <n-form-item-grid-item label="时间窗口">
          <n-input-group>
            <n-input-number 
              v-model:value="timeWindowValue" 
              :min="1" 
              placeholder="数值"
              style="width: 70%"
            />
            <n-select
              v-model:value="timeWindowUnit"
              :options="timeUnitOptions"
              style="width: 30%"
            />
          </n-input-group>
        </n-form-item-grid-item>

        <n-form-item-grid-item label="聚合间隔">
          <n-input-group>
            <n-input-number 
              v-model:value="intervalValue" 
              :min="1" 
              placeholder="数值"
              style="width: 70%"
            />
            <n-select
              v-model:value="intervalUnit"
              :options="timeUnitOptions"
              style="width: 30%"
            />
          </n-input-group>
        </n-form-item-grid-item>
      </n-grid>

      <n-form-item label="聚合方法" :show-label="true">
        <n-checkbox-group v-model:value="config.methods">
          <n-space item-style="display: flex;">
            <n-checkbox value="avg" label="平均值 (AVG)" />
            <n-checkbox value="max" label="最大值 (MAX)" />
            <n-checkbox value="min" label="最小值 (MIN)" />
            <n-checkbox value="sum" label="求和 (SUM)" />
            <n-checkbox value="count" label="计数 (COUNT)" />
            <n-checkbox value="first" label="首值 (FIRST)" />
            <n-checkbox value="last" label="末值 (LAST)" />
          </n-space>
        </n-checkbox-group>
      </n-form-item>

      <n-form-item label="分组字段" :show-label="true">
        <n-select
          v-model:value="config.group_by"
          multiple
          filterable
          placeholder="选择分组字段"
          :options="fieldOptions"
        />
      </n-form-item>
    </n-card>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { NCard, NGrid, NFormItemGridItem, NInputGroup, NInputNumber, NSelect, NFormItem, NCheckboxGroup, NCheckbox, NSpace } from 'naive-ui'

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
  time_window: '1h',
  interval: '5m',
  methods: ['avg'],
  group_by: []
}

// 内部响应式状态
const config = ref({ ...defaultConfig, ...(props.value || {}) })

// 时间单位选项
const timeUnitOptions = [
  { label: '秒', value: 's' },
  { label: '分', value: 'm' },
  { label: '小时', value: 'h' },
  { label: '天', value: 'd' }
]

// 解析时间字符串 (e.g., "1h" -> { value: 1, unit: "h" })
const parseTime = (str) => {
  if (!str) return { value: 1, unit: 'h' }
  const match = str.match(/^(\d+)([smhd])$/)
  return match ? { value: parseInt(match[1]), unit: match[2] } : { value: 1, unit: 'h' }
}

// 时间窗口拆分状态
const twState = ref(parseTime(config.value.time_window))
const timeWindowValue = computed({
  get: () => twState.value.value,
  set: (val) => { twState.value.value = val; updateTimeWindow() }
})
const timeWindowUnit = computed({
  get: () => twState.value.unit,
  set: (val) => { twState.value.unit = val; updateTimeWindow() }
})
const updateTimeWindow = () => {
  config.value.time_window = `${timeWindowValue.value}${timeWindowUnit.value}`
}

// 聚合间隔拆分状态
const intState = ref(parseTime(config.value.interval))
const intervalValue = computed({
  get: () => intState.value.value,
  set: (val) => { intState.value.value = val; updateInterval() }
})
const intervalUnit = computed({
  get: () => intState.value.unit,
  set: (val) => { intState.value.unit = val; updateInterval() }
})
const updateInterval = () => {
  config.value.interval = `${intervalValue.value}${intervalUnit.value}`
}

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

// 监听 props.value 变化（外部更新）
watch(() => props.value, (newVal) => {
  if (newVal) {
    const merged = { ...defaultConfig, ...newVal }
    // 只有当真的有变化时才更新，防止循环
    if (JSON.stringify(merged) !== JSON.stringify(config.value)) {
      config.value = merged
      // 更新拆分状态
      twState.value = parseTime(merged.time_window)
      intState.value = parseTime(merged.interval)
    }
  }
}, { deep: true })

</script>

<style scoped>
.aggregation-config-editor {
  margin-top: 10px;
}
</style>
