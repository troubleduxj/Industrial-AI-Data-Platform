<template>
  <div class="data-annotation">
    <!-- 页面头部 -->
    <div v-permission="{ action: 'read', resource: 'data_annotation' }" class="page-header">
      <n-space justify="space-between" align="center">
        <div>
          <h2>数据标注</h2>
          <p class="page-description">为AI模型训练提供高质量的标注数据</p>
        </div>
        <n-space>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/annotation-projects"
            type="primary"
            @click="createNewProject"
          >
            <template #icon>
              <n-icon><add-outline /></n-icon>
            </template>
            新建项目
          </PermissionButton>
          <PermissionButton
            permission="POST /api/v2/ai-monitor/annotation-data"
            @click="importData"
          >
            <template #icon>
              <n-icon><cloud-upload-outline /></n-icon>
            </template>
            导入数据
          </PermissionButton>
          <PermissionButton
            permission="GET /api/v2/ai-monitor/annotation-projects"
            @click="refreshData"
          >
            <template #icon>
              <n-icon><refresh-outline /></n-icon>
            </template>
            刷新
          </PermissionButton>
        </n-space>
      </n-space>
    </div>

    <!-- 统计概览 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item>
        <n-card>
          <n-statistic label="标注项目" :value="stats.totalProjects">
            <template #prefix>
              <n-icon color="#18a058">
                <folder-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="已标注数据" :value="stats.annotatedData">
            <template #prefix>
              <n-icon color="#2080f0">
                <checkmark-done-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="待标注数据" :value="stats.pendingData">
            <template #prefix>
              <n-icon color="#f0a020">
                <time-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="标注准确率" :value="stats.accuracy" suffix="%">
            <template #prefix>
              <n-icon color="#d03050">
                <analytics-outline />
              </n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 主要内容区域 -->
    <n-grid :cols="4" :x-gap="16" class="main-content">
      <!-- 左侧：项目列表 -->
      <n-grid-item :span="1">
        <n-card title="标注项目" class="project-list-card">
          <template #header-extra>
            <n-input
              v-model:value="projectSearchKeyword"
              placeholder="搜索项目"
              size="small"
              clearable
            >
              <template #prefix>
                <n-icon><search-outline /></n-icon>
              </template>
            </n-input>
          </template>

          <n-list>
            <n-list-item
              v-for="project in filteredProjects"
              :key="project.id"
              :class="{ 'active-project': currentProject?.id === project.id }"
              @click="selectProject(project)"
            >
              <n-space justify="space-between" align="center" style="width: 100%">
                <div>
                  <n-text strong>{{ project.name }}</n-text>
                  <br />
                  <n-text depth="3" style="font-size: 12px">
                    {{ project.type }} · {{ project.dataCount }}条数据
                  </n-text>
                </div>
                <n-tag :type="getProjectStatusType(project.status)" size="small">
                  {{ getProjectStatusText(project.status) }}
                </n-tag>
              </n-space>
            </n-list-item>
          </n-list>

          <div v-if="filteredProjects.length === 0" class="no-projects">
            <n-empty description="暂无项目" size="small" />
          </div>
        </n-card>
      </n-grid-item>

      <!-- 中间：标注工作区 -->
      <n-grid-item :span="2">
        <n-card title="标注工作区" class="annotation-workspace">
          <template #header-extra>
            <n-space v-if="currentProject">
              <n-text depth="3" style="font-size: 12px">
                进度: {{ currentProject.progress }}%
              </n-text>
              <n-progress
                type="line"
                :percentage="currentProject.progress"
                :show-indicator="false"
                style="width: 100px"
              />
              <PermissionButton
                permission="POST /api/v2/ai-monitor/annotation-data"
                size="small"
                :disabled="!hasUnsavedChanges"
                @click="saveAnnotation"
              >
                <template #icon>
                  <n-icon><save-outline /></n-icon>
                </template>
                保存
              </PermissionButton>
            </n-space>
          </template>

          <div v-if="!currentProject" class="no-project-selected">
            <n-empty description="请选择一个标注项目" size="large">
              <template #icon>
                <n-icon size="48">
                  <document-text-outline />
                </n-icon>
              </template>
            </n-empty>
          </div>

          <div v-else class="annotation-content">
            <!-- 数据导航 -->
            <div class="data-navigation">
              <n-space justify="space-between" align="center">
                <n-space>
                  <n-button size="small" :disabled="currentDataIndex <= 0" @click="previousData">
                    <template #icon>
                      <n-icon><chevron-back-outline /></n-icon>
                    </template>
                    上一条
                  </n-button>
                  <n-button
                    size="small"
                    :disabled="currentDataIndex >= currentProject.dataCount - 1"
                    @click="nextData"
                  >
                    下一条
                    <template #icon>
                      <n-icon><chevron-forward-outline /></n-icon>
                    </template>
                  </n-button>
                </n-space>
                <n-text depth="3" style="font-size: 12px">
                  {{ currentDataIndex + 1 }} / {{ currentProject.dataCount }}
                </n-text>
              </n-space>
            </div>

            <!-- 数据展示区域 -->
            <div class="data-display">
              <DataViewer
                :data="currentData"
                :project-type="currentProject.type"
                @data-change="handleDataChange"
              />
            </div>

            <!-- 标注工具栏 -->
            <div class="annotation-toolbar">
              <AnnotationTools
                :project="currentProject"
                :current-annotation="currentAnnotation"
                @annotation-change="handleAnnotationChange"
              />
            </div>
          </div>
        </n-card>
      </n-grid-item>

      <!-- 右侧：标注信息 -->
      <n-grid-item :span="1">
        <n-space vertical size="large">
          <!-- 当前标注信息 -->
          <n-card title="标注信息" size="small">
            <div v-if="!currentProject">
              <n-empty description="请选择项目" size="small" />
            </div>
            <div v-else>
              <n-descriptions :column="1" size="small">
                <n-descriptions-item label="项目类型">
                  {{ getProjectTypeText(currentProject.type) }}
                </n-descriptions-item>
                <n-descriptions-item label="当前数据">
                  {{ currentDataIndex + 1 }} / {{ currentProject.dataCount }}
                </n-descriptions-item>
                <n-descriptions-item label="标注状态">
                  <n-tag
                    :type="currentAnnotation?.status === 'completed' ? 'success' : 'warning'"
                    size="small"
                  >
                    {{ currentAnnotation?.status === 'completed' ? '已完成' : '待标注' }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="标注者">
                  {{ currentAnnotation?.annotator || '未分配' }}
                </n-descriptions-item>
              </n-descriptions>
            </div>
          </n-card>

          <!-- 标注历史 -->
          <n-card title="标注历史" size="small">
            <AnnotationHistory :annotations="annotationHistory" :loading="historyLoading" />
          </n-card>

          <!-- 质量检查 -->
          <n-card title="质量检查" size="small">
            <QualityCheck :project="currentProject" :current-annotation="currentAnnotation" />
          </n-card>
        </n-space>
      </n-grid-item>
    </n-grid>

    <!-- 项目创建对话框 -->
    <ProjectCreator v-model:show="showProjectCreator" @project-created="handleProjectCreated" />

    <!-- 数据导入对话框 -->
    <DataImporter
      v-model:show="showDataImporter"
      :project="currentProject"
      @data-imported="handleDataImported"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NSpace,
  NButton,
  NIcon,
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NInput,
  NList,
  NListItem,
  NText,
  NTag,
  NEmpty,
  NProgress,
  NDescriptions,
  NDescriptionsItem,
  useMessage,
} from 'naive-ui'
import {
  AddOutline,
  CloudUploadOutline,
  RefreshOutline,
  FolderOutline,
  CheckmarkDoneOutline,
  TimeOutline,
  AnalyticsOutline,
  SearchOutline,
  DocumentTextOutline,
  SaveOutline,
  ChevronBackOutline,
  ChevronForwardOutline,
} from '@vicons/ionicons5'
import PermissionButton from '@/components/common/PermissionButton.vue'
import DataViewer from './components/DataViewer.vue'
import AnnotationTools from './components/AnnotationTools.vue'
import AnnotationHistory from './components/AnnotationHistory.vue'
import QualityCheck from './components/QualityCheck.vue'
import ProjectCreator from './components/ProjectCreator.vue'
import DataImporter from './components/DataImporter.vue'

// 响应式数据
const loading = ref(false)
const historyLoading = ref(false)
const hasUnsavedChanges = ref(false)
const showProjectCreator = ref(false)
const showDataImporter = ref(false)
const projectSearchKeyword = ref('')
const currentProject = ref(null)
const currentDataIndex = ref(0)
const currentData = ref(null)
const currentAnnotation = ref(null)
const projects = ref([])
const annotationHistory = ref([])

// 统计数据
const stats = ref({
  totalProjects: 0,
  annotatedData: 0,
  pendingData: 0,
  accuracy: 0,
})

// 消息提示
const message = useMessage()

// 过滤后的项目列表
const filteredProjects = computed(() => {
  if (!projectSearchKeyword.value) {
    return projects.value
  }

  const keyword = projectSearchKeyword.value.toLowerCase()
  return projects.value.filter(
    (project) =>
      project.name.toLowerCase().includes(keyword) || project.type.toLowerCase().includes(keyword)
  )
})

// 生成模拟项目数据
const generateProjects = () => {
  const projectTypes = ['classification', 'detection', 'segmentation', 'regression']
  const statuses = ['active', 'completed', 'paused']

  const projectList = []
  for (let i = 1; i <= 8; i++) {
    projectList.push({
      id: i,
      name: `标注项目${i}`,
      type: projectTypes[i % projectTypes.length],
      status: statuses[i % statuses.length],
      dataCount: Math.floor(Math.random() * 1000) + 100,
      progress: Math.floor(Math.random() * 100),
      createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      annotator: `标注员${Math.floor(Math.random() * 5) + 1}`,
    })
  }

  return projectList
}

// 生成模拟标注历史
const generateAnnotationHistory = () => {
  const history = []
  for (let i = 1; i <= 10; i++) {
    history.push({
      id: i,
      dataId: Math.floor(Math.random() * 100) + 1,
      action: Math.random() > 0.5 ? 'annotated' : 'reviewed',
      annotator: `标注员${Math.floor(Math.random() * 3) + 1}`,
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      quality: Math.random() > 0.3 ? 'good' : 'needs_review',
    })
  }

  return history
}

// 获取项目状态类型
const getProjectStatusType = (status) => {
  const statusMap = {
    active: 'info',
    completed: 'success',
    paused: 'warning',
  }
  return statusMap[status] || 'default'
}

// 获取项目状态文本
const getProjectStatusText = (status) => {
  const statusMap = {
    active: '进行中',
    completed: '已完成',
    paused: '已暂停',
  }
  return statusMap[status] || status
}

// 获取项目类型文本
const getProjectTypeText = (type) => {
  const typeMap = {
    classification: '分类标注',
    detection: '目标检测',
    segmentation: '图像分割',
    regression: '回归标注',
  }
  return typeMap[type] || type
}

// 选择项目
const selectProject = (project) => {
  currentProject.value = project
  currentDataIndex.value = 0
  loadCurrentData()
  loadAnnotationHistory()
}

// 加载当前数据
const loadCurrentData = () => {
  if (!currentProject.value) return

  // 模拟加载数据
  currentData.value = {
    id: currentDataIndex.value + 1,
    type: currentProject.value.type,
    content: generateMockDataContent(currentProject.value.type),
    metadata: {
      source: 'device_001',
      timestamp: new Date().toISOString(),
      quality: Math.random() > 0.3 ? 'high' : 'medium',
    },
  }

  // 模拟加载标注
  currentAnnotation.value = {
    id: Date.now(),
    dataId: currentData.value.id,
    status: Math.random() > 0.3 ? 'completed' : 'pending',
    annotator: currentProject.value.annotator,
    labels: generateMockLabels(currentProject.value.type),
    confidence: Math.random() * 0.3 + 0.7,
    createdAt: new Date().toISOString(),
  }
}

// 生成模拟数据内容
const generateMockDataContent = (type) => {
  switch (type) {
    case 'classification':
      return {
        values: Array.from({ length: 10 }, () => Math.random() * 100),
        features: ['温度', '压力', '振动', '电流', '电压', '转速', '功率', '效率', '噪音', '湿度'],
      }
    case 'detection':
      return {
        imageUrl: '/api/mock/image.jpg',
        width: 800,
        height: 600,
      }
    case 'segmentation':
      return {
        imageUrl: '/api/mock/image.jpg',
        width: 800,
        height: 600,
        regions: [],
      }
    case 'regression':
      return {
        timeSeries: Array.from({ length: 100 }, (_, i) => ({
          timestamp: new Date(Date.now() - (100 - i) * 60000).toISOString(),
          value: Math.sin(i * 0.1) * 50 + Math.random() * 10 + 50,
        })),
      }
    default:
      return {}
  }
}

// 生成模拟标签
const generateMockLabels = (type) => {
  switch (type) {
    case 'classification':
      return {
        category: ['正常', '异常', '警告'][Math.floor(Math.random() * 3)],
        confidence: Math.random() * 0.3 + 0.7,
      }
    case 'detection':
      return {
        boxes: [
          {
            x: Math.random() * 400,
            y: Math.random() * 300,
            width: Math.random() * 200 + 50,
            height: Math.random() * 200 + 50,
            label: '异常区域',
            confidence: Math.random() * 0.3 + 0.7,
          },
        ],
      }
    case 'segmentation':
      return {
        masks: [
          {
            points: Array.from({ length: 8 }, () => ({
              x: Math.random() * 800,
              y: Math.random() * 600,
            })),
            label: '关键区域',
          },
        ],
      }
    case 'regression':
      return {
        targetValue: Math.random() * 100,
        predictedValue: Math.random() * 100,
        error: Math.random() * 10,
      }
    default:
      return {}
  }
}

// 上一条数据
const previousData = () => {
  if (currentDataIndex.value > 0) {
    currentDataIndex.value--
    loadCurrentData()
  }
}

// 下一条数据
const nextData = () => {
  if (currentDataIndex.value < currentProject.value.dataCount - 1) {
    currentDataIndex.value++
    loadCurrentData()
  }
}

// 处理数据变化
const handleDataChange = (data) => {
  currentData.value = { ...currentData.value, ...data }
  hasUnsavedChanges.value = true
}

// 处理标注变化
const handleAnnotationChange = (annotation) => {
  currentAnnotation.value = { ...currentAnnotation.value, ...annotation }
  hasUnsavedChanges.value = true
}

// 保存标注
const saveAnnotation = async () => {
  try {
    // 模拟保存过程
    await new Promise((resolve) => setTimeout(resolve, 1000))

    hasUnsavedChanges.value = false
    message.success('标注已保存')

    // 更新项目进度
    if (currentProject.value && currentAnnotation.value.status === 'completed') {
      const completedCount =
        Math.floor((currentProject.value.dataCount * currentProject.value.progress) / 100) + 1
      currentProject.value.progress = Math.min(
        100,
        Math.floor((completedCount / currentProject.value.dataCount) * 100)
      )
    }
  } catch (error) {
    message.error('保存失败')
  }
}

// 加载标注历史
const loadAnnotationHistory = () => {
  historyLoading.value = true
  setTimeout(() => {
    annotationHistory.value = generateAnnotationHistory()
    historyLoading.value = false
  }, 500)
}

// 创建新项目
const createNewProject = () => {
  showProjectCreator.value = true
}

// 导入数据
const importData = () => {
  if (!currentProject.value) {
    message.warning('请先选择一个项目')
    return
  }
  showDataImporter.value = true
}

// 处理项目创建
const handleProjectCreated = (project) => {
  projects.value.unshift(project)
  stats.value.totalProjects++
  message.success('项目创建成功')
}

// 处理数据导入
const handleDataImported = (data) => {
  if (currentProject.value) {
    currentProject.value.dataCount += data.count
    stats.value.pendingData += data.count
    message.success(`成功导入 ${data.count} 条数据`)
  }
}

// 刷新数据
const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    projects.value = generateProjects()
    loadAnnotationHistory()
    loading.value = false
    message.success('数据刷新成功')
  }, 1000)
}

// 组件挂载时初始化数据
onMounted(() => {
  projects.value = generateProjects()
  annotationHistory.value = generateAnnotationHistory()

  // 初始化统计数据
  stats.value = {
    totalProjects: projects.value.length,
    annotatedData: 1247,
    pendingData: 583,
    accuracy: 94.2,
  }

  // 默认选择第一个项目
  if (projects.value.length > 0) {
    selectProject(projects.value[0])
  }
})
</script>

<style scoped>
.data-annotation {
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
}

.page-description {
  color: #666;
  margin: 4px 0 0 0;
  font-size: 14px;
}

.stats-grid {
  margin-bottom: 16px;
}

.main-content {
  margin-bottom: 16px;
}

.project-list-card {
  height: fit-content;
}

.active-project {
  background-color: #f0f8ff;
  border-radius: 6px;
}

.no-projects {
  padding: 20px 0;
}

.annotation-workspace {
  min-height: 600px;
}

.no-project-selected {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.annotation-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.data-navigation {
  padding: 12px;
  background-color: #fafafa;
  border-radius: 6px;
}

.data-display {
  flex: 1;
  min-height: 300px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 16px;
}

.annotation-toolbar {
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}
</style>
