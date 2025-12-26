<template>
  <n-modal
    v-model:show="showModal"
    title="TDengine 结构差异比对"
    preset="card"
    style="width: 900px"
    @after-leave="handleClose"
  >
    <div v-if="loading" class="flex justify-center p-8">
      <n-spin size="large" description="正在比对结构..." />
    </div>

    <div v-else-if="error" class="p-4">
      <n-result status="error" title="比对失败" :description="error">
        <template #footer>
          <n-button @click="fetchDiff">重试</n-button>
        </template>
      </n-result>
    </div>

    <div v-else class="space-y-6">
      <n-alert type="info" class="mb-4">
        <template #icon>
          <n-icon :component="InformationCircleOutline" />
        </template>
        当前比对对象：设备类型 <strong>{{ deviceTypeCode }}</strong>
        <span class="ml-4 text-gray-500">TDengine表名: {{ diffData?.stable_name }}</span>
      </n-alert>

      <n-alert v-if="diffData?.table_exists === false" type="warning" title="TDengine超级表不存在" class="mb-4">
        该设备类型对应的超级表 <strong>{{ diffData?.stable_name }}</strong> 在TDengine中不存在。
        <br>
        所有系统字段将被视为"TDengine缺失字段"。请先执行同步操作创建表结构。
      </n-alert>

      <!-- 1. TDengine缺失字段 (System 有, TDengine 无) -->
      <n-card title="TDengine 缺失字段 (系统已定义但数据库不存在)" size="small">
        <template #header-extra>
          <n-tag :type="diffData?.diff?.missing_in_tdengine?.length ? 'error' : 'success'">
            {{ diffData?.diff?.missing_in_tdengine?.length || 0 }} 个
          </n-tag>
        </template>
        <n-data-table
          v-if="diffData?.diff?.missing_in_tdengine?.length"
          :columns="missingInTdColumns"
          :data="diffData.diff.missing_in_tdengine"
          :max-height="300"
          size="small"
        />
        <n-empty v-else description="无缺失字段" />
      </n-card>

      <!-- 2. 系统缺失字段 (TDengine 有, System 无) -->
      <n-card title="系统缺失字段 (数据库存在但系统未定义)" size="small" class="mt-4">
        <template #header-extra>
          <n-tag :type="diffData?.diff?.missing_in_system?.length ? 'warning' : 'success'">
            {{ diffData?.diff?.missing_in_system?.length || 0 }} 个
          </n-tag>
        </template>
        <n-data-table
          v-if="diffData?.diff?.missing_in_system?.length"
          :columns="missingInSystemColumns"
          :data="diffData.diff.missing_in_system"
          :max-height="300"
          size="small"
        />
        <n-empty v-else description="无缺失字段" />
      </n-card>
    </div>
  </n-modal>
</template>

<script setup>
import { ref, computed, watch, h } from 'vue'
import { NModal, NCard, NDataTable, NTag, NEmpty, NSpin, NResult, NAlert, NIcon, NButton } from 'naive-ui'
import { InformationCircleOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'

const props = defineProps({
  show: Boolean,
  deviceTypeCode: String
})

const emit = defineEmits(['update:show'])

const showModal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const loading = ref(false)
const error = ref(null)
const diffData = ref(null)

const missingInTdColumns = [
  { title: '字段代码', key: 'field_code' },
  { title: '字段名称', key: 'field_name' },
  { title: '系统类型', key: 'field_type' }
]

const missingInSystemColumns = [
  { title: '字段代码', key: 'field_code' },
  { title: 'TDengine类型', key: 'td_type' },
  { 
    title: 'TAG', 
    key: 'is_tag',
    render: (row) => row.is_tag ? '是' : '否'
  }
]

const fetchDiff = async () => {
  if (!props.deviceTypeCode) return
  
  loading.value = true
  error.value = null
  try {
    const res = await dataModelApi.getSchemaDiff(props.deviceTypeCode)
    if (res.success) {
      diffData.value = res.data
    } else {
      error.value = res.message
    }
  } catch (err) {
    error.value = err.message || '请求失败'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.show,
  (val) => {
    if (val && props.deviceTypeCode) {
      fetchDiff()
    }
  }
)

const handleClose = () => {
  // reset state if needed
}
</script>

<style scoped>
.mt-4 {
  margin-top: 16px;
}
</style>
