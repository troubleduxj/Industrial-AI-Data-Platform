<template>
  <div class="unified-config p-4">
    <n-card :bordered="false" class="mb-4">
      <n-space vertical>
        <n-alert type="info" show-icon class="mb-4" v-if="!selectedDeviceType">
          请先选择设备类型以配置其元数据、模型及报警规则。
        </n-alert>
        
        <n-form-item label="当前配置对象 (设备类型)" label-placement="left" label-width="180">
          <n-select
            v-model:value="selectedDeviceType"
            placeholder="请选择设备类型"
            :options="deviceTypeOptions"
            filterable
            clearable
            style="width: 300px"
            @update:value="handleDeviceTypeChange"
          />
          <n-button class="ml-4" type="primary" ghost @click="fetchDeviceTypes">
            <template #icon>
              <n-icon :component="RefreshOutline" />
            </template>
            刷新列表
          </n-button>
        </n-form-item>
      </n-space>
    </n-card>

    <div v-if="selectedDeviceType" class="config-content">
      <n-card :bordered="false">
        <n-tabs type="line" animated v-model:value="activeTab">
          <n-tab-pane name="fields" tab="字段定义">
            <div class="tab-content">
              <FieldConfig :device-type-code="selectedDeviceType" embedded />
            </div>
          </n-tab-pane>
          <n-tab-pane name="models" tab="模型配置">
            <div class="tab-content">
              <ModelConfig :device-type-code="selectedDeviceType" embedded />
            </div>
          </n-tab-pane>
          <n-tab-pane name="alarms" tab="报警规则">
            <div class="tab-content">
              <AlarmRules :device-type-code="selectedDeviceType" embedded />
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-card>
    </div>
    
    <GlobalDashboard v-else @select="handleGlobalSelect" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NCard, NSpace, NAlert, NFormItem, NSelect, NButton, NIcon, 
  NTabs, NTabPane, NEmpty, useMessage 
} from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { deviceTypeApi } from '@/api/device-v2'
import FieldConfig from '@/views/metadata/fields/index.vue'
import ModelConfig from '@/views/metadata/models/index.vue'
import AlarmRules from '@/views/alarm/alarm-rules/index.vue'
import GlobalDashboard from './components/GlobalDashboard.vue'

defineOptions({ name: '统一配置管理' })

const route = useRoute()
const message = useMessage()

console.log('UnifiedConfig Page Loaded. Route Name:', route.name)
console.log('UnifiedConfig Page Component Name:', 'UnifiedConfig')
console.log('Route Meta KeepAlive:', route.meta.keepAlive)
const selectedDeviceType = ref(null)
const deviceTypeOptions = ref([])
const activeTab = ref('fields')

const fetchDeviceTypes = async () => {
  try {
    const res = await deviceTypeApi.list({
      page: 1,
      page_size: 100,
      is_active: true
    })
    if (res.success) {
      deviceTypeOptions.value = res.data.map(item => ({
        label: item.type_name,
        value: item.type_code,
        tdengine_stable_name: item.tdengine_stable_name
      }))
    }
  } catch (error) {
    console.error('获取设备类型列表失败:', error)
    message.error('获取设备类型列表失败')
  }
}

const handleDeviceTypeChange = (val) => {
  // Can add logic here if needed
}

const handleGlobalSelect = ({ deviceType, tab }) => {
  selectedDeviceType.value = deviceType
  if (tab) {
    activeTab.value = tab
  }
}

onMounted(async () => {
  await fetchDeviceTypes()
  if (route.query.device_type) {
    selectedDeviceType.value = route.query.device_type
  }
  if (route.query.tab) {
    activeTab.value = route.query.tab
  }
})
</script>

<style scoped>
.unified-config {
  min-height: 100%;
}
.tab-content {
  padding-top: 16px;
}
</style>
