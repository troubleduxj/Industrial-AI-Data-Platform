<script setup>
import { nextTick } from 'vue'
import { NButton, NCard, NInput, NSelect } from 'naive-ui'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  deviceTypeOptions: {
    type: Array,
    default: () => [
      { label: '全部设备', value: '' },
      { label: '焊机', value: 'welding' },
      { label: '服务器', value: 'server' },
      { label: '网络设备', value: 'network' },
      { label: '存储设备', value: 'storage' },
      { label: '安全设备', value: 'security' },
      { label: '其他', value: 'other' },
    ],
  },
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

const handleSearch = () => {
  const searchParams = {
    device_name: props.modelValue.device_name?.trim(),
    device_code: props.modelValue.device_code?.trim(),
    manufacturer: props.modelValue.manufacturer?.trim(),
    device_type: props.modelValue.device_type,
    device_model: props.modelValue.device_model?.trim(),
    online_address: props.modelValue.online_address?.trim(),
  }

  // 过滤掉空值
  const filteredParams = Object.fromEntries(
    Object.entries(searchParams).filter(([_, v]) => v !== undefined && v !== '')
  )

  console.log('搜索参数:', filteredParams)
  emit('search', filteredParams)
}

const handleReset = () => {
  const emptyValues = {
    device_name: '',
    device_code: '',
    manufacturer: '',
    device_type: '',
    device_model: '',
    online_address: '',
  }
  emit('update:modelValue', emptyValues)
  emit('reset')
  // 确保UI更新
  nextTick(() => {
    emit('update:modelValue', emptyValues)
  })
}

const updateValue = (key, value) => {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <NCard class="mb-15" rounded-10>
    <div flex flex-wrap items-center gap-15>
      <QueryBarItem label="设备名称" :label-width="70">
        <NInput
          :value="modelValue.device_name"
          clearable
          type="text"
          placeholder="请输入设备名称"
          @update:value="(val) => updateValue('device_name', val)"
          @keypress.enter="handleSearch"
        />
      </QueryBarItem>
      <QueryBarItem label="设备厂家" :label-width="70">
        <NInput
          :value="modelValue.manufacturer"
          clearable
          type="text"
          placeholder="请输入设备厂家"
          @update:value="(val) => updateValue('manufacturer', val)"
          @keypress.enter="handleSearch"
        />
      </QueryBarItem>
      <QueryBarItem label="设备编码" :label-width="70">
        <NInput
          :value="modelValue.device_code"
          clearable
          type="text"
          placeholder="请输入设备编码"
          @update:value="(val) => updateValue('device_code', val)"
          @keypress.enter="handleSearch"
        />
      </QueryBarItem>
      <QueryBarItem label="设备类型" :label-width="70">
        <NSelect
          :value="modelValue.device_type"
          style="width: 180px"
          :options="props.deviceTypeOptions"
          clearable
          placeholder="请选择设备类型"
          @update:value="(val) => updateValue('device_type', val)"
        />
      </QueryBarItem>
      <QueryBarItem label="设备型号" :label-width="70">
        <NInput
          :value="modelValue.device_model"
          clearable
          type="text"
          placeholder="请输入设备型号"
          @update:value="(val) => updateValue('device_model', val)"
          @keypress.enter="handleSearch"
        />
      </QueryBarItem>
      <QueryBarItem label="在线地址" :label-width="70">
        <NInput
          :value="modelValue.online_address"
          clearable
          type="text"
          placeholder="请输入在线地址"
          @update:value="(val) => updateValue('online_address', val)"
          @keypress.enter="handleSearch"
        />
      </QueryBarItem>

      <div class="ml-20 flex items-center gap-10">
        <NButton type="primary" @click="handleSearch">
          <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
        </NButton>
        <NButton @click="handleReset">
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
        </NButton>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.query-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
[flex~='wrap'] {
  flex-wrap: wrap;
}
</style>
