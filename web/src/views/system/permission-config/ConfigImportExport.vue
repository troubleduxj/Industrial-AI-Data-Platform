<template>
  <div class="config-import-export">
    <CommonPage show-footer title="权限配置导入导出" class="import-export-page">
      <template #action>
        <div class="flex items-center gap-3">
          <NButton type="primary" @click="handleExportAll">
            <TheIcon icon="material-symbols:download" :size="18" class="mr-1" />
            导出全部配置
          </NButton>
          <NButton @click="handleImportConfig">
            <TheIcon icon="material-symbols:upload" :size="18" class="mr-1" />
            导入配置
          </NButton>
          <NButton @click="handleCreateTemplate">
            <TheIcon icon="material-symbols:description" :size="18" class="mr-1" />
            生成模板
          </NButton>
        </div>
      </template>

      <div class="import-export-content">
        <NGrid :cols="2" :x-gap="24" :y-gap="24">
          <!-- 导出配置 -->
          <NGi>
            <NCard title="导出配置" class="export-card">
              <div class="export-options">
                <h4>选择导出内容</h4>
                <NCheckboxGroup v-model:value="exportOptions">
                  <NSpace vertical>
                    <NCheckbox value="roles">角色权限配置</NCheckbox>
                    <NCheckbox value="apis">API权限配置</NCheckbox>
                    <NCheckbox value="menus">菜单权限配置</NCheckbox>
                    <NCheckbox value="data">数据权限配置</NCheckbox>
                    <NCheckbox value="users">用户权限分配</NCheckbox>
                  </NSpace>
                </NCheckboxGroup>

                <NDivider />

                <h4>导出格式</h4>
                <NRadioGroup v-model:value="exportFormat">
                  <NSpace vertical>
                    <NRadio value="json">JSON格式</NRadio>
                    <NRadio value="yaml">YAML格式</NRadio>
                    <NRadio value="excel">Excel格式</NRadio>
                  </NSpace>
                </NRadioGroup>

                <NDivider />

                <h4>导出选项</h4>
                <NSpace vertical>
                  <NCheckbox v-model:checked="includeMetadata">包含元数据</NCheckbox>
                  <NCheckbox v-model:checked="compressOutput">压缩输出</NCheckbox>
                  <NCheckbox v-model:checked="encryptOutput">加密导出</NCheckbox>
                </NSpace>

                <div v-if="encryptOutput" class="encrypt-options">
                  <NFormItem label="加密密码">
                    <NInput
                      v-model:value="encryptPassword"
                      type="password"
                      placeholder="请输入加密密码"
                    />
                  </NFormItem>
                </div>
              </div>

              <template #action>
                <NSpace>
                  <NButton type="primary" :loading="exporting" @click="handleExport">
                    开始导出
                  </NButton>
                  <NButton @click="handlePreviewExport"> 预览导出 </NButton>
                </NSpace>
              </template>
            </NCard>
          </NGi>

          <!-- 导入配置 -->
          <NGi>
            <NCard title="导入配置" class="import-card">
              <div class="import-options">
                <h4>上传配置文件</h4>
                <NUpload
                  :file-list="importFileList"
                  :max="1"
                  accept=".json,.yaml,.yml,.xlsx"
                  @change="handleFileChange"
                  @remove="handleFileRemove"
                >
                  <NUploadDragger>
                    <div class="upload-content">
                      <TheIcon icon="material-symbols:upload-file" :size="48" class="upload-icon" />
                      <p class="upload-text">点击或拖拽文件到此区域上传</p>
                      <p class="upload-hint">支持 JSON、YAML、Excel 格式</p>
                    </div>
                  </NUploadDragger>
                </NUpload>

                <div v-if="importPreview" class="import-preview">
                  <NDivider />
                  <h4>导入预览</h4>
                  <div class="preview-stats">
                    <NStatistic label="角色配置" :value="importPreview.roles?.length || 0" />
                    <NStatistic label="API配置" :value="importPreview.apis?.length || 0" />
                    <NStatistic label="菜单配置" :value="importPreview.menus?.length || 0" />
                    <NStatistic label="用户配置" :value="importPreview.users?.length || 0" />
                  </div>

                  <NDivider />
                  <h4>导入选项</h4>
                  <NSpace vertical>
                    <NCheckbox v-model:checked="mergeMode">合并模式（保留现有配置）</NCheckbox>
                    <NCheckbox v-model:checked="validateBeforeImport">导入前验证</NCheckbox>
                    <NCheckbox v-model:checked="createBackup">创建备份</NCheckbox>
                  </NSpace>

                  <div v-if="validationErrors.length > 0" class="validation-errors">
                    <NDivider />
                    <h4>验证错误</h4>
                    <NAlert type="error">
                      <ul>
                        <li v-for="error in validationErrors" :key="error">{{ error }}</li>
                      </ul>
                    </NAlert>
                  </div>
                </div>
              </div>

              <template #action>
                <NSpace>
                  <NButton
                    type="primary"
                    :loading="importing"
                    :disabled="!importPreview || validationErrors.length > 0"
                    @click="handleImport"
                  >
                    开始导入
                  </NButton>
                  <NButton :disabled="!importPreview" @click="handleValidateImport">
                    验证配置
                  </NButton>
                </NSpace>
              </template>
            </NCard>
          </NGi>
        </NGrid>

        <!-- 历史记录 -->
        <NCard title="导入导出历史" class="history-card">
          <NTable :data="historyRecords" :columns="historyColumns" />
        </NCard>

        <!-- 配置模板 -->
        <NCard title="配置模板" class="template-card">
          <div class="template-list">
            <div v-for="template in configTemplates" :key="template.id" class="template-item">
              <div class="template-info">
                <h4 class="template-name">{{ template.name }}</h4>
                <p class="template-desc">{{ template.description }}</p>
                <div class="template-meta">
                  <NTag size="small">{{ template.type }}</NTag>
                  <span class="template-size">{{ template.size }}</span>
                </div>
              </div>
              <div class="template-actions">
                <NButton size="small" @click="handleDownloadTemplate(template)">
                  <TheIcon icon="material-symbols:download" :size="16" class="mr-1" />
                  下载
                </NButton>
                <NButton size="small" @click="handlePreviewTemplate(template)">
                  <TheIcon icon="material-symbols:preview" :size="16" class="mr-1" />
                  预览
                </NButton>
              </div>
            </div>
          </div>
        </NCard>
      </div>
    </CommonPage>

    <!-- 导出预览模态框 -->
    <NModal v-model:show="exportPreviewVisible" preset="card" title="导出预览" style="width: 80%">
      <div class="export-preview">
        <NTabs type="line">
          <NTabPane name="content" tab="导出内容">
            <NCode :code="exportPreviewContent" :language="exportFormat" />
          </NTabPane>
          <NTabPane name="stats" tab="统计信息">
            <div class="export-stats">
              <NGrid :cols="4" :x-gap="16">
                <NGi>
                  <NStatistic label="总配置数" :value="exportStats.total" />
                </NGi>
                <NGi>
                  <NStatistic label="文件大小" :value="exportStats.size" />
                </NGi>
                <NGi>
                  <NStatistic label="压缩率" :value="exportStats.compression" />
                </NGi>
                <NGi>
                  <NStatistic label="预计时间" :value="exportStats.estimatedTime" />
                </NGi>
              </NGrid>
            </div>
          </NTabPane>
        </NTabs>
      </div>

      <template #action>
        <NSpace>
          <NButton @click="exportPreviewVisible = false">取消</NButton>
          <NButton type="primary" @click="handleConfirmExport">确认导出</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 模板预览模态框 -->
    <NModal v-model:show="templatePreviewVisible" preset="card" title="模板预览" style="width: 70%">
      <div class="template-preview">
        <NCode :code="templatePreviewContent" language="json" />
      </div>
    </NModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NButton,
  NCard,
  NGrid,
  NGi,
  NCheckboxGroup,
  NCheckbox,
  NRadioGroup,
  NRadio,
  NSpace,
  NDivider,
  NFormItem,
  NInput,
  NUpload,
  NUploadDragger,
  NStatistic,
  NAlert,
  NTable,
  NTag,
  NTabs,
  NTabPane,
  NCode,
  NModal,
  useMessage,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import systemV2Api from '@/api/system-v2'
import { formatDate, formatFileSize } from '@/utils'

defineOptions({ name: 'ConfigImportExport' })

const $message = useMessage()

// 导出配置
const exportOptions = ref(['roles', 'apis', 'menus'])
const exportFormat = ref('json')
const includeMetadata = ref(true)
const compressOutput = ref(false)
const encryptOutput = ref(false)
const encryptPassword = ref('')
const exporting = ref(false)

// 导入配置
const importFileList = ref([])
const importPreview = ref(null)
const importing = ref(false)
const mergeMode = ref(true)
const validateBeforeImport = ref(true)
const createBackup = ref(true)
const validationErrors = ref([])

// 预览和模板
const exportPreviewVisible = ref(false)
const exportPreviewContent = ref('')
const exportStats = ref({})
const templatePreviewVisible = ref(false)
const templatePreviewContent = ref('')

// 历史记录
const historyRecords = ref([])
const historyColumns = [
  { title: '操作类型', key: 'type' },
  { title: '文件名', key: 'filename' },
  { title: '大小', key: 'size', render: (row) => formatFileSize(row.size) },
  { title: '状态', key: 'status' },
  { title: '操作时间', key: 'created_at', render: (row) => formatDate(row.created_at) },
  { title: '操作人', key: 'operator' },
]

// 配置模板
const configTemplates = ref([
  {
    id: 1,
    name: '基础权限模板',
    description: '包含基本的角色和权限配置',
    type: '基础模板',
    size: '2.5KB',
  },
  {
    id: 2,
    name: '完整权限模板',
    description: '包含所有类型的权限配置示例',
    type: '完整模板',
    size: '15.2KB',
  },
  {
    id: 3,
    name: '部门权限模板',
    description: '多部门权限隔离配置模板',
    type: '部门模板',
    size: '8.7KB',
  },
])

// 生命周期
onMounted(() => {
  loadHistory()
})

// 方法
async function loadHistory() {
  try {
    const response = await systemV2Api.getImportExportHistory()
    historyRecords.value = response.data || []
  } catch (error) {
    console.error('Load history error:', error)
  }
}

async function handleExportAll() {
  exportOptions.value = ['roles', 'apis', 'menus', 'data', 'users']
  await handleExport()
}

async function handleExport() {
  if (exportOptions.value.length === 0) {
    $message.warning('请选择要导出的内容')
    return
  }

  try {
    exporting.value = true

    const exportData = {
      options: exportOptions.value,
      format: exportFormat.value,
      includeMetadata: includeMetadata.value,
      compress: compressOutput.value,
      encrypt: encryptOutput.value,
      password: encryptPassword.value,
    }

    const response = await systemV2Api.exportPermissionConfig(exportData)

    // 下载文件
    const blob = new Blob([response.data], {
      type: getContentType(exportFormat.value),
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `permission-config-${new Date().toISOString().split('T')[0]}.${exportFormat.value}`
    a.click()
    URL.revokeObjectURL(url)

    $message.success('配置导出成功')
    await loadHistory()
  } catch (error) {
    $message.error('导出配置失败')
    console.error('Export error:', error)
  } finally {
    exporting.value = false
  }
}

async function handlePreviewExport() {
  if (exportOptions.value.length === 0) {
    $message.warning('请选择要导出的内容')
    return
  }

  try {
    const exportData = {
      options: exportOptions.value,
      format: exportFormat.value,
      includeMetadata: includeMetadata.value,
      preview: true,
    }

    const response = await systemV2Api.previewExportConfig(exportData)

    exportPreviewContent.value = response.data.content
    exportStats.value = response.data.stats
    exportPreviewVisible.value = true
  } catch (error) {
    $message.error('生成导出预览失败')
    console.error('Preview export error:', error)
  }
}

async function handleConfirmExport() {
  exportPreviewVisible.value = false
  await handleExport()
}

function handleImportConfig() {
  // 触发文件选择
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json,.yaml,.yml,.xlsx'
  input.onchange = (e) => {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      handleFileChange({ fileList: files.map((file) => ({ file })) })
    }
  }
  input.click()
}

async function handleFileChange({ fileList }) {
  importFileList.value = fileList

  if (fileList.length > 0) {
    const file = fileList[0].file

    try {
      const content = await readFileContent(file)
      const parsed = parseFileContent(content, getFileExtension(file.name))

      importPreview.value = parsed
      validationErrors.value = []

      if (validateBeforeImport.value) {
        await handleValidateImport()
      }
    } catch (error) {
      $message.error('文件解析失败')
      console.error('Parse file error:', error)
      importPreview.value = null
    }
  }
}

function handleFileRemove() {
  importFileList.value = []
  importPreview.value = null
  validationErrors.value = []
}

async function handleValidateImport() {
  if (!importPreview.value) {
    $message.warning('请先上传配置文件')
    return
  }

  try {
    const response = await systemV2Api.validateImportConfig(importPreview.value)
    validationErrors.value = response.data.errors || []

    if (validationErrors.value.length === 0) {
      $message.success('配置验证通过')
    } else {
      $message.error(`发现 ${validationErrors.value.length} 个验证错误`)
    }
  } catch (error) {
    $message.error('配置验证失败')
    console.error('Validate import error:', error)
  }
}

async function handleImport() {
  if (!importPreview.value) {
    $message.warning('请先上传配置文件')
    return
  }

  if (validationErrors.value.length > 0) {
    $message.error('请先修复验证错误')
    return
  }

  try {
    importing.value = true

    const importData = {
      config: importPreview.value,
      options: {
        mergeMode: mergeMode.value,
        createBackup: createBackup.value,
      },
    }

    await systemV2Api.importPermissionConfig(importData)

    $message.success('配置导入成功')

    // 清理状态
    importFileList.value = []
    importPreview.value = null
    validationErrors.value = []

    await loadHistory()
  } catch (error) {
    $message.error('导入配置失败')
    console.error('Import error:', error)
  } finally {
    importing.value = false
  }
}

async function handleCreateTemplate() {
  try {
    const response = await systemV2Api.generateConfigTemplate()

    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'permission-config-template.json'
    a.click()
    URL.revokeObjectURL(url)

    $message.success('配置模板生成成功')
  } catch (error) {
    $message.error('生成配置模板失败')
    console.error('Create template error:', error)
  }
}

async function handleDownloadTemplate(template) {
  try {
    const response = await systemV2Api.getConfigTemplate(template.id)

    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${template.name}.json`
    a.click()
    URL.revokeObjectURL(url)

    $message.success('模板下载成功')
  } catch (error) {
    $message.error('下载模板失败')
    console.error('Download template error:', error)
  }
}

async function handlePreviewTemplate(template) {
  try {
    const response = await systemV2Api.getConfigTemplate(template.id)
    templatePreviewContent.value = JSON.stringify(response.data, null, 2)
    templatePreviewVisible.value = true
  } catch (error) {
    $message.error('预览模板失败')
    console.error('Preview template error:', error)
  }
}

// 工具方法
function readFileContent(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = reject
    reader.readAsText(file)
  })
}

function parseFileContent(content, extension) {
  switch (extension) {
    case 'json':
      return JSON.parse(content)
    case 'yaml':
    case 'yml':
      // 这里需要引入yaml解析库
      throw new Error('YAML格式暂不支持')
    case 'xlsx':
      // 这里需要引入Excel解析库
      throw new Error('Excel格式暂不支持')
    default:
      throw new Error('不支持的文件格式')
  }
}

function getFileExtension(filename) {
  return filename.split('.').pop().toLowerCase()
}

function getContentType(format) {
  const types = {
    json: 'application/json',
    yaml: 'application/x-yaml',
    excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  }
  return types[format] || 'application/octet-stream'
}
</script>

<style scoped>
.config-import-export {
  padding: 16px;
}

.import-export-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.export-card,
.import-card {
  height: fit-content;
}

.export-options,
.import-options {
  padding: 16px 0;
}

.export-options h4,
.import-options h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 500;
}

.encrypt-options {
  margin-top: 12px;
}

.upload-content {
  text-align: center;
  padding: 32px;
}

.upload-icon {
  color: var(--text-color-secondary);
  margin-bottom: 16px;
}

.upload-text {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.import-preview {
  margin-top: 16px;
}

.preview-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 16px 0;
}

.validation-errors ul {
  margin: 0;
  padding-left: 20px;
}

.history-card,
.template-card {
  margin-top: 24px;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.template-info {
  flex: 1;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.template-desc {
  margin: 0 0 8px 0;
  color: var(--text-color-secondary);
  font-size: 14px;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-size {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.template-actions {
  display: flex;
  gap: 8px;
}

.export-preview,
.template-preview {
  padding: 16px 0;
}

.export-stats {
  padding: 16px 0;
}

.mr-1 {
  margin-right: 4px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.gap-3 {
  gap: 12px;
}
</style>
