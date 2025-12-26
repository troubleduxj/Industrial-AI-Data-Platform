<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    title="版本管理"
    style="width: 900px"
    :mask-closable="false"
    @after-leave="handleClose"
  >
    <div class="version-manager">
      <!-- 工具栏 -->
      <div class="toolbar">
        <n-button type="primary" @click="createVersion">
          + 创建版本快照
        </n-button>
        <n-button @click="loadVersions">
          ↻ 刷新
        </n-button>
      </div>

      <!-- 版本列表 -->
      <n-data-table
        :loading="loading"
        :columns="columns"
        :data="versions"
        :max-height="400"
        :row-key="(row) => row.id"
      />

      <!-- 分页 -->
      <div class="pagination">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.total"
          :page-sizes="[10, 20, 50]"
          show-size-picker
          @update:page="loadVersions"
          @update:page-size="loadVersions"
        />
      </div>

      <!-- 版本对比按钮 -->
      <div v-if="selectedVersions.length === 2" class="compare-action">
        <n-button type="primary" @click="compareSelectedVersions">
          对比选中的两个版本
        </n-button>
        <n-button @click="selectedVersions = []">清除选择</n-button>
      </div>
    </div>

    <!-- 创建版本对话框 -->
    <n-modal
      v-model:show="createDialogVisible"
      preset="dialog"
      title="创建版本快照"
      style="width: 500px"
    >
      <n-form :model="createForm" label-placement="left" label-width="100px">
        <n-form-item label="版本名称">
          <n-input v-model:value="createForm.version_name" placeholder="请输入版本名称" />
        </n-form-item>
        <n-form-item label="版本描述">
          <n-input 
            v-model:value="createForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入版本描述" 
          />
        </n-form-item>
        <n-form-item label="变更摘要">
          <n-input 
            v-model:value="createForm.change_summary" 
            type="textarea" 
            :rows="2"
            placeholder="简要描述本次变更内容" 
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="createDialogVisible = false">取消</n-button>
        <n-button type="primary" @click="submitCreateVersion" :loading="creating">
          创建
        </n-button>
      </template>
    </n-modal>

    <!-- 版本详情对话框 -->
    <n-modal
      v-model:show="detailDialogVisible"
      preset="card"
      title="版本详情"
      style="width: 700px"
    >
      <n-descriptions v-if="currentVersion" :column="2" bordered>
        <n-descriptions-item label="版本号">{{ currentVersion.version }}</n-descriptions-item>
        <n-descriptions-item label="版本名称">{{ currentVersion.version_name }}</n-descriptions-item>
        <n-descriptions-item label="变更类型">
          <n-tag :type="getChangeTypeTag(currentVersion.change_type)" size="small">
            {{ getChangeTypeLabel(currentVersion.change_type) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="创建人">{{ currentVersion.created_by_name }}</n-descriptions-item>
        <n-descriptions-item label="创建时间" :span="2">{{ formatTime(currentVersion.created_at) }}</n-descriptions-item>
        <n-descriptions-item label="版本描述" :span="2">{{ currentVersion.description || '-' }}</n-descriptions-item>
        <n-descriptions-item label="变更摘要" :span="2">{{ currentVersion.change_summary || '-' }}</n-descriptions-item>
      </n-descriptions>
      <div v-if="currentVersion?.snapshot" class="snapshot-info">
        <h4>快照信息</h4>
        <n-descriptions :column="3" bordered>
          <n-descriptions-item label="节点数量">
            {{ currentVersion.snapshot.nodes?.length || 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="连接数量">
            {{ currentVersion.snapshot.connections?.length || 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="触发类型">
            {{ currentVersion.snapshot.trigger_type || '-' }}
          </n-descriptions-item>
        </n-descriptions>
      </div>
    </n-modal>

    <!-- 版本对比对话框 -->
    <n-modal
      v-model:show="compareDialogVisible"
      preset="card"
      title="版本对比"
      style="width: 800px"
    >
      <div v-if="compareResult" class="compare-result">
        <div class="compare-header">
          <div class="version-info">
            <strong>版本 {{ compareResult.version1?.version }}</strong>
            <span>{{ formatTime(compareResult.version1?.created_at) }}</span>
          </div>
          <div class="vs">VS</div>
          <div class="version-info">
            <strong>版本 {{ compareResult.version2?.version }}</strong>
            <span>{{ formatTime(compareResult.version2?.created_at) }}</span>
          </div>
        </div>
        
        <n-divider />
        
        <div class="compare-summary">
          <n-statistic label="总变更数" :value="compareResult.summary?.total_changes || 0" />
          <n-statistic label="新增节点" :value="compareResult.summary?.nodes_added || 0" />
          <n-statistic label="删除节点" :value="compareResult.summary?.nodes_removed || 0" />
        </div>
        
        <n-divider />
        
        <div class="changes-list">
          <h4>变更详情</h4>
          <n-data-table :columns="diffColumns" :data="compareResult.changes || []" :max-height="300" />
        </div>
      </div>
    </n-modal>
  </n-modal>
</template>

<script setup>
import { ref, reactive, watch, h, computed } from 'vue'
import { NButton, NTag } from 'naive-ui'
import { getWorkflowVersions, getWorkflowVersionDetail, createWorkflowVersion, rollbackWorkflowVersion, compareWorkflowVersions } from '@/api/workflow'

const $message = window.$message

const props = defineProps({
  modelValue: Boolean,
  workflowId: [Number, String],
})

const emit = defineEmits(['update:modelValue', 'rollback'])

const visible = ref(false)
const loading = ref(false)
const versions = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

// 创建版本
const createDialogVisible = ref(false)
const creating = ref(false)
const createForm = reactive({
  version_name: '',
  description: '',
  change_summary: '',
})

// 版本详情
const detailDialogVisible = ref(false)
const currentVersion = ref(null)

// 版本对比
const selectedVersions = ref([])
const compareDialogVisible = ref(false)
const compareResult = ref(null)

// 表格列定义
const columns = computed(() => [
  { title: '版本号', key: 'version', width: 100 },
  { title: '版本名称', key: 'version_name', minWidth: 150 },
  { 
    title: '变更类型', 
    key: 'change_type', 
    width: 100,
    render: (row) => h(NTag, { type: getChangeTypeTag(row.change_type), size: 'small' }, () => getChangeTypeLabel(row.change_type))
  },
  { title: '节点数', key: 'node_count', width: 80, align: 'center' },
  { 
    title: '状态', 
    key: 'status', 
    width: 120,
    render: (row) => {
      const tags = []
      if (row.is_current) tags.push(h(NTag, { type: 'success', size: 'small' }, () => '当前版本'))
      if (row.is_published) tags.push(h(NTag, { type: 'warning', size: 'small' }, () => '已发布'))
      return h('div', { style: 'display: flex; gap: 4px;' }, tags)
    }
  },
  { title: '创建人', key: 'created_by_name', width: 100 },
  { 
    title: '创建时间', 
    key: 'created_at', 
    width: 160,
    render: (row) => formatTime(row.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right',
    render: (row) => h('div', { style: 'display: flex; gap: 8px;' }, [
      h(NButton, { text: true, type: 'primary', size: 'small', onClick: () => viewVersion(row) }, () => '查看'),
      h(NButton, { 
        text: true, 
        type: 'primary', 
        size: 'small', 
        disabled: selectedVersions.value.length >= 2 && !selectedVersions.value.includes(row.id),
        onClick: () => selectForCompare(row) 
      }, () => selectedVersions.value.includes(row.id) ? '取消对比' : '对比'),
      h(NButton, { 
        text: true, 
        type: 'warning', 
        size: 'small', 
        disabled: row.is_current,
        onClick: () => rollbackVersion(row) 
      }, () => '回滚'),
    ])
  }
])

// 对比表格列
const diffColumns = [
  { title: '字段', key: 'field', width: 120 },
  { 
    title: '变更类型', 
    key: 'type', 
    width: 120,
    render: (row) => h(NTag, { type: getDiffTypeTag(row.type), size: 'small' }, () => getDiffTypeLabel(row.type))
  },
  { title: '旧值', key: 'old_value', render: (row) => formatDiffValue(row.old_value) },
  { title: '新值', key: 'new_value', render: (row) => formatDiffValue(row.new_value || row.value) },
]

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val && props.workflowId) {
    loadVersions()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const loadVersions = async () => {
  if (!props.workflowId) return
  
  loading.value = true
  try {
    const res = await getWorkflowVersions(props.workflowId, {
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    if (res.code === 200) {
      versions.value = res.data?.items || []
      pagination.total = res.data?.total || 0
    }
  } catch (error) {
    console.error('加载版本列表失败:', error)
  } finally {
    loading.value = false
  }
}

const createVersion = () => {
  createForm.version_name = ''
  createForm.description = ''
  createForm.change_summary = ''
  createDialogVisible.value = true
}

const submitCreateVersion = async () => {
  creating.value = true
  try {
    const res = await createWorkflowVersion(props.workflowId, createForm)
    if (res.code === 200) {
      $message?.success('创建版本成功')
      createDialogVisible.value = false
      loadVersions()
    } else {
      $message?.error(res.message || '创建失败')
    }
  } catch (error) {
    $message?.error('创建版本失败')
  } finally {
    creating.value = false
  }
}

const viewVersion = async (row) => {
  try {
    const res = await getWorkflowVersionDetail(props.workflowId, row.id)
    if (res.code === 200) {
      currentVersion.value = res.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    $message?.error('获取版本详情失败')
  }
}

const selectForCompare = (row) => {
  const index = selectedVersions.value.indexOf(row.id)
  if (index > -1) {
    selectedVersions.value.splice(index, 1)
  } else if (selectedVersions.value.length < 2) {
    selectedVersions.value.push(row.id)
  }
}

const compareSelectedVersions = async () => {
  if (selectedVersions.value.length !== 2) return
  
  try {
    const res = await compareWorkflowVersions(
      props.workflowId,
      selectedVersions.value[0],
      selectedVersions.value[1]
    )
    if (res.code === 200) {
      compareResult.value = res.data
      compareDialogVisible.value = true
    }
  } catch (error) {
    $message?.error('版本对比失败')
  }
}

const rollbackVersion = async (row) => {
  if (!confirm(`确定要回滚到版本 ${row.version} 吗？当前版本将被保存为历史版本。`)) {
    return
  }
  
  try {
    const res = await rollbackWorkflowVersion(props.workflowId, row.id)
    if (res.code === 200) {
      $message?.success('回滚成功')
      loadVersions()
      emit('rollback', res.data)
    } else {
      $message?.error(res.message || '回滚失败')
    }
  } catch (error) {
    $message?.error('回滚失败')
  }
}

const handleClose = () => {
  selectedVersions.value = []
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const getChangeTypeLabel = (type) => {
  const labels = { create: '创建', update: '更新', publish: '发布', rollback: '回滚' }
  return labels[type] || type || '-'
}

const getChangeTypeTag = (type) => {
  const tags = { create: 'success', update: 'info', publish: 'warning', rollback: 'default' }
  return tags[type] || 'default'
}

const getDiffTypeLabel = (type) => {
  const labels = { modified: '修改', added: '新增', removed: '删除', count_changed: '数量变化' }
  return labels[type] || type || '-'
}

const getDiffTypeTag = (type) => {
  const tags = { modified: 'warning', added: 'success', removed: 'error', count_changed: 'info' }
  return tags[type] || 'default'
}

const formatDiffValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
</script>

<style scoped>
.version-manager .toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.version-manager .pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.version-manager .compare-action {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.snapshot-info {
  margin-top: 16px;
}

.snapshot-info h4 {
  margin-bottom: 12px;
  color: #303133;
}

.compare-result .compare-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.compare-result .compare-header .version-info {
  text-align: center;
  flex: 1;
}

.compare-result .compare-header .version-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.compare-result .compare-header .version-info span {
  color: #909399;
  font-size: 12px;
}

.compare-result .compare-header .vs {
  padding: 0 20px;
  font-weight: bold;
  color: #409eff;
}

.compare-result .compare-summary {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;
}

.compare-result .changes-list h4 {
  margin-bottom: 12px;
  color: #303133;
}
</style>
