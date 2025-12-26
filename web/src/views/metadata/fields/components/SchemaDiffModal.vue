<template>
  <n-modal
    :show="show"
    title="TDengine 结构比对"
    preset="card"
    style="width: 800px"
    @update:show="updateShow"
    @after-enter="handleEnter"
  >
    <n-spin :show="loading">
      <div v-if="diffResult" class="diff-content">
        <!-- 概览 -->
        <n-alert :type="getAlertType(diffResult)" class="mb-4">
          <template #header>
            {{ getAlertTitle(diffResult) }}
          </template>
          {{ getAlertContent(diffResult) }}
        </n-alert>

        <!-- 差异详情 -->
        <n-tabs type="line" animated>
          <!-- 仅在系统存在 -->
          <n-tab-pane name="system_only" :tab="`系统独有 (${diffResult.system_only?.length || 0})`">
            <n-empty v-if="!diffResult.system_only?.length" description="无差异" />
            <n-list v-else>
              <n-list-item v-for="field in diffResult.system_only" :key="field.field_code">
                <n-thing :title="field.field_code" :description="field.field_name">
                  <template #header-extra>
                    <n-tag type="info">{{ field.field_type }}</n-tag>
                  </template>
                  <template #description>
                    {{ field.field_name }} ({{ field.description || '无描述' }})
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <!-- 仅在TDengine存在 -->
          <n-tab-pane name="tdengine_only" :tab="`TDengine独有 (${diffResult.tdengine_only?.length || 0})`">
            <n-empty v-if="!diffResult.tdengine_only?.length" description="无差异" />
            <n-list v-else>
              <n-list-item v-for="field in diffResult.tdengine_only" :key="field.field_code">
                <n-thing :title="field.field_code">
                  <template #header-extra>
                    <n-tag type="success">{{ field.type_name }}</n-tag>
                  </template>
                  <template #description>
                    长度: {{ field.length }} | 备注: {{ field.note || '-' }}
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>

          <!-- 类型不一致 -->
          <n-tab-pane name="type_mismatch" :tab="`类型不一致 (${diffResult.type_mismatch?.length || 0})`">
            <n-empty v-if="!diffResult.type_mismatch?.length" description="无差异" />
            <n-list v-else>
              <n-list-item v-for="field in diffResult.type_mismatch" :key="field.field_code">
                <n-thing :title="field.field_code" :description="field.field_name">
                  <template #description>
                    <div class="flex items-center gap-2">
                      <n-tag type="info" size="small">系统: {{ field.system_type }}</n-tag>
                      <span class="text-gray-400">vs</span>
                      <n-tag type="success" size="small">TDengine: {{ field.tdengine_type }}</n-tag>
                    </div>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-tab-pane>
        </n-tabs>
      </div>
      <div v-else-if="!loading" class="text-center py-8 text-gray-400">
        暂无数据
      </div>
    </n-spin>

    <template #footer>
      <n-space justify="end">
        <n-button @click="updateShow(false)">关闭</n-button>
        <n-button type="primary" @click="fetchDiff" :loading="loading">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
          重新比对
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { NModal, NSpin, NAlert, NTabs, NTabPane, NList, NListItem, NThing, NTag, NEmpty, NSpace, NButton, NIcon, useMessage } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { dataModelApi } from '@/api/v2/data-model'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  deviceTypeCode: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:show'])
const message = useMessage()

const loading = ref(false)
const diffResult = ref(null)

const updateShow = (val) => {
  emit('update:show', val)
}

const handleEnter = () => {
  if (props.deviceTypeCode) {
    fetchDiff()
  }
}

const fetchDiff = async () => {
  if (!props.deviceTypeCode) return
  
  loading.value = true
  try {
    const res = await dataModelApi.getSchemaDiff(props.deviceTypeCode)
    if (res.success) {
      diffResult.value = res.data
    } else {
      message.error(res.message || '获取比对结果失败')
    }
  } catch (error) {
    message.error('获取比对结果失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const getAlertType = (result) => {
  if (!result) return 'info'
  const hasDiff = (result.system_only?.length > 0) || 
                 (result.tdengine_only?.length > 0) || 
                 (result.type_mismatch?.length > 0)
  return hasDiff ? 'warning' : 'success'
}

const getAlertTitle = (result) => {
  if (!result) return '加载中...'
  const hasDiff = (result.system_only?.length > 0) || 
                 (result.tdengine_only?.length > 0) || 
                 (result.type_mismatch?.length > 0)
  return hasDiff ? '发现结构差异' : '结构一致'
}

const getAlertContent = (result) => {
  if (!result) return ''
  const parts = []
  if (result.system_only?.length) parts.push(`系统多出 ${result.system_only.length} 个字段`)
  if (result.tdengine_only?.length) parts.push(`TDengine多出 ${result.tdengine_only.length} 个字段`)
  if (result.type_mismatch?.length) parts.push(`存在 ${result.type_mismatch.length} 个类型不一致`)
  
  return parts.length ? parts.join('，') : '系统配置与TDengine表结构完全一致'
}
</script>

<style scoped>
.diff-content {
  min-height: 300px;
}
</style>
