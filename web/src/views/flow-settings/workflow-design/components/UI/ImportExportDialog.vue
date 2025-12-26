<template>
  <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
    <div class="dialog-container">
      <div class="dialog-header">
        <span class="dialog-title">{{ isImport ? '导入工作流' : '导出工作流' }}</span>
        <button class="close-btn" @click="handleClose">×</button>
      </div>
      
      <div class="dialog-content">
        <!-- 导入模式 -->
        <template v-if="isImport">
          <div class="import-section">
            <div class="upload-area" 
              :class="{ dragover: isDragover }"
              @dragover.prevent="isDragover = true"
              @dragleave="isDragover = false"
              @drop.prevent="handleFileDrop"
            >
              <div class="upload-icon">📁</div>
              <div class="upload-text">拖拽 JSON 文件到此处</div>
              <div class="upload-hint">或</div>
              <label class="upload-btn">
                <input type="file" accept=".json" @change="handleFileSelect" hidden />
                选择文件
              </label>
            </div>
            
            <div v-if="importData" class="preview-section">
              <div class="preview-header">
                <span>预览</span>
                <button class="clear-btn" @click="clearImport">清除</button>
              </div>
              <div class="preview-info">
                <div class="info-item">
                  <span class="info-label">名称:</span>
                  <span class="info-value">{{ importData.name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">节点数:</span>
                  <span class="info-value">{{ importData.nodes?.length || 0 }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">连接数:</span>
                  <span class="info-value">{{ importData.connections?.length || 0 }}</span>
                </div>
                <div v-if="importData.description" class="info-item">
                  <span class="info-label">描述:</span>
                  <span class="info-value">{{ importData.description }}</span>
                </div>
              </div>
              <div v-if="importError" class="import-error">
                <span class="error-icon">⚠️</span>
                <span>{{ importError }}</span>
              </div>
            </div>
          </div>
        </template>
        
        <!-- 导出模式 -->
        <template v-else>
          <div class="export-section">
            <div class="export-options">
              <div class="option-group">
                <label class="option-label">导出格式</label>
                <div class="option-buttons">
                  <button 
                    class="option-btn" 
                    :class="{ active: exportFormat === 'json' }"
                    @click="exportFormat = 'json'"
                  >
                    JSON
                  </button>
                  <button 
                    class="option-btn" 
                    :class="{ active: exportFormat === 'yaml' }"
                    @click="exportFormat = 'yaml'"
                    disabled
                  >
                    YAML (开发中)
                  </button>
                </div>
              </div>
              
              <div class="option-group">
                <label class="option-label">导出内容</label>
                <div class="checkbox-group">
                  <label class="checkbox-item">
                    <input type="checkbox" v-model="exportOptions.includeMetadata" />
                    <span>包含元数据</span>
                  </label>
                  <label class="checkbox-item">
                    <input type="checkbox" v-model="exportOptions.includePositions" />
                    <span>包含节点位置</span>
                  </label>
                  <label class="checkbox-item">
                    <input type="checkbox" v-model="exportOptions.prettyPrint" />
                    <span>格式化输出</span>
                  </label>
                </div>
              </div>
            </div>
            
            <div class="export-preview">
              <div class="preview-header">
                <span>预览</span>
                <button class="copy-btn" @click="copyToClipboard">📋 复制</button>
              </div>
              <pre class="preview-code">{{ exportPreview }}</pre>
            </div>
          </div>
        </template>
      </div>
      
      <div class="dialog-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button 
          class="btn-confirm" 
          :disabled="isImport ? !importData || !!importError : false"
          @click="handleConfirm"
        >
          {{ isImport ? '导入' : '下载' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Props
const props = defineProps<{
  visible: boolean
  mode: 'import' | 'export'
  workflowData?: any
}>()

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'import', data: any): void
  (e: 'export'): void
}>()

// 状态
const isDragover = ref(false)
const importData = ref<any>(null)
const importError = ref('')
const exportFormat = ref('json')
const exportOptions = ref({
  includeMetadata: true,
  includePositions: true,
  prettyPrint: true
})

// 计算属性
const isImport = computed(() => props.mode === 'import')

const exportPreview = computed(() => {
  if (!props.workflowData) return '{}'
  
  const data: any = {
    name: props.workflowData.name || '未命名工作流',
    description: props.workflowData.description || '',
    nodes: props.workflowData.nodes || [],
    connections: props.workflowData.connections || []
  }
  
  if (exportOptions.value.includeMetadata) {
    data.version = '1.0'
    data.exportedAt = new Date().toISOString()
  }
  
  if (!exportOptions.value.includePositions) {
    data.nodes = data.nodes.map((n: any) => {
      const { x, y, ...rest } = n
      return rest
    })
  }
  
  return exportOptions.value.prettyPrint 
    ? JSON.stringify(data, null, 2)
    : JSON.stringify(data)
})

// 方法
function handleClose() {
  clearImport()
  emit('close')
}

function handleFileDrop(event: DragEvent) {
  isDragover.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    processFile(input.files[0])
  }
}

function processFile(file: File) {
  if (!file.name.endsWith('.json')) {
    importError.value = '请选择 JSON 文件'
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string)
      validateImportData(data)
    } catch (error) {
      importError.value = 'JSON 格式无效'
      importData.value = null
    }
  }
  reader.readAsText(file)
}

function validateImportData(data: any) {
  importError.value = ''
  
  if (!data.name) {
    importError.value = '缺少工作流名称'
  } else if (!Array.isArray(data.nodes)) {
    importError.value = '缺少节点数据'
  } else if (!Array.isArray(data.connections)) {
    importError.value = '缺少连接数据'
  }
  
  if (!importError.value) {
    importData.value = data
  }
}

function clearImport() {
  importData.value = null
  importError.value = ''
}

function copyToClipboard() {
  navigator.clipboard.writeText(exportPreview.value)
    .then(() => {
      alert('已复制到剪贴板')
    })
    .catch(() => {
      alert('复制失败')
    })
}

function handleConfirm() {
  if (isImport.value) {
    if (importData.value) {
      emit('import', importData.value)
      handleClose()
    }
  } else {
    downloadFile()
    emit('export')
  }
}

function downloadFile() {
  const blob = new Blob([exportPreview.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.workflowData?.name || 'workflow'}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 监听 visible 变化，重置状态
watch(() => props.visible, (val) => {
  if (!val) {
    clearImport()
  }
})
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-container {
  width: 560px;
  max-height: 80vh;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 20px;
  color: #8c8c8c;
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #262626;
}

.dialog-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel, .btn-confirm {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  border: 1px solid #d9d9d9;
  background: #fff;
  color: #595959;
}

.btn-cancel:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-confirm {
  border: none;
  background: #1890ff;
  color: #fff;
}

.btn-confirm:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-confirm:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

/* 导入样式 */
.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  transition: all 0.2s;
}

.upload-area.dragover {
  border-color: #1890ff;
  background: #e6f7ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  color: #262626;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #8c8c8c;
  margin-bottom: 12px;
}

.upload-btn {
  display: inline-block;
  padding: 8px 20px;
  background: #1890ff;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.upload-btn:hover {
  background: #40a9ff;
}

.preview-section {
  margin-top: 20px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 500;
}

.clear-btn, .copy-btn {
  padding: 4px 12px;
  border: none;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.clear-btn:hover, .copy-btn:hover {
  background: #e8e8e8;
}

.preview-info {
  padding: 16px;
}

.info-item {
  display: flex;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  width: 60px;
  color: #8c8c8c;
  flex-shrink: 0;
}

.info-value {
  color: #262626;
}

.import-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  color: #ff4d4f;
  border-top: 1px solid #ffccc7;
}

/* 导出样式 */
.export-options {
  margin-bottom: 20px;
}

.option-group {
  margin-bottom: 16px;
}

.option-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 8px;
}

.option-buttons {
  display: flex;
  gap: 8px;
}

.option-btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.option-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.option-btn.active {
  border-color: #1890ff;
  background: #e6f7ff;
  color: #1890ff;
}

.option-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-item input {
  width: 16px;
  height: 16px;
}

.export-preview {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.preview-code {
  margin: 0;
  padding: 16px;
  background: #fafafa;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
