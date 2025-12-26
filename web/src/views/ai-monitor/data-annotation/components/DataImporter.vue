<template>
  <n-modal
    v-model:show="showModal"
    preset="card"
    title="导入数据"
    style="width: 700px"
    :mask-closable="false"
  >
    <n-steps :current="currentStep" size="small">
      <n-step title="选择导入方式" />
      <n-step title="配置参数" />
      <n-step title="预览数据" />
      <n-step title="确认导入" />
    </n-steps>

    <div class="step-content">
      <!-- 步骤1: 选择导入方式 -->
      <div v-if="currentStep === 1" class="import-method">
        <n-grid cols="2" x-gap="16" y-gap="16">
          <n-grid-item>
            <n-card
              :class="{ active: importMethod === 'upload' }"
              hoverable
              @click="importMethod = 'upload'"
            >
              <template #header>
                <n-space align="center">
                  <n-icon size="24">
                    <cloud-upload-outline />
                  </n-icon>
                  <n-text>本地上传</n-text>
                </n-space>
              </template>
              <n-text depth="3">从本地选择文件上传</n-text>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card
              :class="{ active: importMethod === 'url' }"
              hoverable
              @click="importMethod = 'url'"
            >
              <template #header>
                <n-space align="center">
                  <n-icon size="24">
                    <link-outline />
                  </n-icon>
                  <n-text>URL导入</n-text>
                </n-space>
              </template>
              <n-text depth="3">通过URL批量导入</n-text>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card
              :class="{ active: importMethod === 'database' }"
              hoverable
              @click="importMethod = 'database'"
            >
              <template #header>
                <n-space align="center">
                  <n-icon size="24">
                    <server-outline />
                  </n-icon>
                  <n-text>数据库导入</n-text>
                </n-space>
              </template>
              <n-text depth="3">从数据库查询导入</n-text>
            </n-card>
          </n-grid-item>

          <n-grid-item>
            <n-card
              :class="{ active: importMethod === 'api' }"
              hoverable
              @click="importMethod = 'api'"
            >
              <template #header>
                <n-space align="center">
                  <n-icon size="24">
                    <code-outline />
                  </n-icon>
                  <n-text>API接口</n-text>
                </n-space>
              </template>
              <n-text depth="3">通过API接口导入</n-text>
            </n-card>
          </n-grid-item>
        </n-grid>
      </div>

      <!-- 步骤2: 配置参数 -->
      <div v-if="currentStep === 2" class="import-config">
        <!-- 本地上传配置 -->
        <div v-if="importMethod === 'upload'">
          <n-form label-placement="left" label-width="100px">
            <n-form-item label="文件类型">
              <n-select
                v-model:value="uploadConfig.fileType"
                :options="fileTypeOptions"
                placeholder="选择文件类型"
              />
            </n-form-item>

            <n-form-item label="上传文件">
              <n-upload
                ref="uploadRef"
                :file-list="uploadConfig.fileList"
                :max="100"
                directory-dnd
                multiple
                @update:file-list="handleFileListChange"
              >
                <n-upload-dragger>
                  <div style="margin-bottom: 12px">
                    <n-icon size="48" :depth="3">
                      <archive-outline />
                    </n-icon>
                  </div>
                  <n-text style="font-size: 16px"> 点击或者拖动文件到该区域来上传 </n-text>
                  <n-p depth="3" style="margin: 8px 0 0 0">
                    支持单个或批量上传，严禁上传敏感信息
                  </n-p>
                </n-upload-dragger>
              </n-upload>
            </n-form-item>
          </n-form>
        </div>

        <!-- URL导入配置 -->
        <div v-if="importMethod === 'url'">
          <n-form label-placement="left" label-width="100px">
            <n-form-item label="URL列表">
              <n-input
                v-model:value="urlConfig.urls"
                type="textarea"
                placeholder="请输入URL列表，每行一个"
                :rows="8"
              />
            </n-form-item>

            <n-form-item label="请求头">
              <n-input v-model:value="urlConfig.headers" placeholder="JSON格式的请求头" />
            </n-form-item>
          </n-form>
        </div>

        <!-- 数据库导入配置 -->
        <div v-if="importMethod === 'database'">
          <n-form label-placement="left" label-width="100px">
            <n-form-item label="数据库类型">
              <n-select
                v-model:value="dbConfig.type"
                :options="dbTypeOptions"
                placeholder="选择数据库类型"
              />
            </n-form-item>

            <n-form-item label="连接字符串">
              <n-input v-model:value="dbConfig.connectionString" placeholder="数据库连接字符串" />
            </n-form-item>

            <n-form-item label="查询语句">
              <n-input
                v-model:value="dbConfig.query"
                type="textarea"
                placeholder="SQL查询语句"
                :rows="4"
              />
            </n-form-item>
          </n-form>
        </div>

        <!-- API接口配置 -->
        <div v-if="importMethod === 'api'">
          <n-form label-placement="left" label-width="100px">
            <n-form-item label="API地址">
              <n-input v-model:value="apiConfig.url" placeholder="API接口地址" />
            </n-form-item>

            <n-form-item label="请求方法">
              <n-select v-model:value="apiConfig.method" :options="methodOptions" />
            </n-form-item>

            <n-form-item label="请求参数">
              <n-input
                v-model:value="apiConfig.params"
                type="textarea"
                placeholder="JSON格式的请求参数"
                :rows="4"
              />
            </n-form-item>
          </n-form>
        </div>
      </div>

      <!-- 步骤3: 预览数据 -->
      <div v-if="currentStep === 3" class="data-preview">
        <n-space vertical>
          <n-alert type="info">
            预览前 {{ Math.min(previewData.length, 10) }} 条数据，共检测到
            {{ previewData.length }} 条数据
          </n-alert>

          <n-data-table
            :columns="previewColumns"
            :data="previewData.slice(0, 10)"
            size="small"
            max-height="300px"
          />
        </n-space>
      </div>

      <!-- 步骤4: 确认导入 -->
      <div v-if="currentStep === 4" class="import-confirm">
        <n-space vertical>
          <n-alert type="success"> 数据验证通过，准备导入 {{ previewData.length }} 条数据 </n-alert>

          <n-form label-placement="left" label-width="120px">
            <n-form-item label="导入模式">
              <n-radio-group v-model:value="importConfig.mode">
                <n-radio value="append">追加模式</n-radio>
                <n-radio value="replace">替换模式</n-radio>
              </n-radio-group>
            </n-form-item>

            <n-form-item label="数据预处理">
              <n-checkbox-group v-model:value="importConfig.preprocessing">
                <n-space vertical>
                  <n-checkbox value="resize">图像尺寸标准化</n-checkbox>
                  <n-checkbox value="format">格式转换</n-checkbox>
                  <n-checkbox value="validate">数据验证</n-checkbox>
                </n-space>
              </n-checkbox-group>
            </n-form-item>
          </n-form>

          <div v-if="importing" class="import-progress">
            <n-progress type="line" :percentage="importProgress" :show-indicator="false" />
            <n-text depth="3" style="font-size: 12px; margin-top: 4px">
              正在导入... {{ importProgress }}%
            </n-text>
          </div>
        </n-space>
      </div>
    </div>

    <template #footer>
      <n-space justify="space-between">
        <n-button v-if="currentStep > 1" :disabled="importing" @click="currentStep--">
          上一步
        </n-button>
        <div></div>
        <n-space>
          <n-button :disabled="importing" @click="handleCancel"> 取消 </n-button>
          <n-button v-if="currentStep < 4" type="primary" :disabled="!canNext" @click="handleNext">
            下一步
          </n-button>
          <n-button v-else type="primary" :loading="importing" @click="handleImport">
            开始导入
          </n-button>
        </n-space>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import {
  NModal,
  NSteps,
  NStep,
  NGrid,
  NGridItem,
  NCard,
  NIcon,
  NText,
  NSpace,
  NForm,
  NFormItem,
  NSelect,
  NUpload,
  NUploadDragger,
  NInput,
  NP,
  NAlert,
  NDataTable,
  NRadioGroup,
  NRadio,
  NCheckboxGroup,
  NCheckbox,
  NProgress,
  NButton,
  useMessage,
} from 'naive-ui'
import {
  CloudUploadOutline,
  LinkOutline,
  ServerOutline,
  CodeOutline,
  ArchiveOutline,
} from '@vicons/ionicons5'

// Message
const message = useMessage()

// Props
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  projectId: {
    type: [String, Number],
    required: true,
  },
})

// Emits
const emit = defineEmits(['update:show', 'data-imported'])

// Modal显示状态
const showModal = ref(props.show)
watch(
  () => props.show,
  (val) => {
    showModal.value = val
  }
)
watch(showModal, (val) => {
  emit('update:show', val)
})

// 当前步骤
const currentStep = ref(1)

// 导入方式
const importMethod = ref('upload')

// 配置数据
const uploadConfig = reactive({
  fileType: 'image',
  fileList: [],
})

const urlConfig = reactive({
  urls: '',
  headers: '{}',
})

const dbConfig = reactive({
  type: 'mysql',
  connectionString: '',
  query: '',
})

const apiConfig = reactive({
  url: '',
  method: 'GET',
  params: '{}',
})

const importConfig = reactive({
  mode: 'append',
  preprocessing: ['validate'],
})

// 选项数据
const fileTypeOptions = [
  { label: '图像文件', value: 'image' },
  { label: '文本文件', value: 'text' },
  { label: 'CSV文件', value: 'csv' },
  { label: 'JSON文件', value: 'json' },
]

const dbTypeOptions = [
  { label: 'MySQL', value: 'mysql' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'MongoDB', value: 'mongodb' },
]

const methodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
]

// 预览数据
const previewData = ref([])
const previewColumns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '文件名', key: 'filename' },
  { title: '类型', key: 'type', width: 100 },
  { title: '大小', key: 'size', width: 100 },
]

// 导入状态
const importing = ref(false)
const importProgress = ref(0)

// 是否可以进入下一步
const canNext = computed(() => {
  if (currentStep.value === 1) {
    return importMethod.value !== ''
  }
  if (currentStep.value === 2) {
    if (importMethod.value === 'upload') {
      return uploadConfig.fileList.length > 0
    }
    if (importMethod.value === 'url') {
      return urlConfig.urls.trim() !== ''
    }
    if (importMethod.value === 'database') {
      return dbConfig.connectionString && dbConfig.query
    }
    if (importMethod.value === 'api') {
      return apiConfig.url !== ''
    }
  }
  if (currentStep.value === 3) {
    return previewData.value.length > 0
  }
  return true
})

// 文件列表变化处理
const handleFileListChange = (fileList) => {
  uploadConfig.fileList = fileList
}

// 下一步处理
const handleNext = async () => {
  if (currentStep.value === 2) {
    // 获取预览数据
    await loadPreviewData()
  }
  currentStep.value++
}

// 加载预览数据
const loadPreviewData = async () => {
  // 模拟加载预览数据
  previewData.value = Array.from({ length: 50 }, (_, i) => ({
    id: i + 1,
    filename: `data_${i + 1}.jpg`,
    type: 'image/jpeg',
    size: `${Math.floor(Math.random() * 1000 + 100)}KB`,
  }))
}

// 处理导入
const handleImport = async () => {
  importing.value = true
  importProgress.value = 0

  try {
    // 模拟导入过程
    const interval = setInterval(() => {
      importProgress.value += 10
      if (importProgress.value >= 100) {
        clearInterval(interval)

        emit('data-imported', {
          projectId: props.projectId,
          method: importMethod.value,
          count: previewData.value.length,
          config: importConfig,
        })

        message.success(`成功导入 ${previewData.value.length} 条数据`)
        importing.value = false
        handleCancel()
      }
    }, 200)
  } catch (error) {
    importing.value = false
    message.error('导入失败: ' + error.message)
  }
}

// 处理取消
const handleCancel = () => {
  showModal.value = false
  currentStep.value = 1
  importMethod.value = 'upload'
  uploadConfig.fileList = []
  previewData.value = []
  importing.value = false
  importProgress.value = 0
}
</script>

<style scoped>
.step-content {
  margin: 24px 0;
  min-height: 300px;
}

.import-method .n-card {
  cursor: pointer;
  transition: all 0.3s;
}

.import-method .n-card.active {
  border-color: #18a058;
}

.import-progress {
  margin-top: 16px;
}
</style>
