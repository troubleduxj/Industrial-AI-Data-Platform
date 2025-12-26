<template>
  <CommonPage title="Shared 层迁移测试" desc="验证工具函数和 API 迁移后的功能">
    <n-space vertical :size="16">
      <!-- 工具函数测试 -->
      <n-card title="1. 工具函数测试（来自 Shared 层）" segmented>
        <n-space vertical>
          <n-alert type="info">
            这些函数现在从 <n-text code>@/utils</n-text> 导入，但实际来自
            <n-text code>packages/shared</n-text>
          </n-alert>

          <n-divider>类型检查</n-divider>
          <div>
            <n-text strong>isEmpty 测试：</n-text>
            <n-space>
              <n-tag :type="testResults.isEmpty ? 'success' : 'error'">
                isEmpty([]) = {{ testResults.isEmpty }}
              </n-tag>
              <n-tag :type="testResults.isValidEmail ? 'success' : 'error'">
                isValidEmail('test@example.com') = {{ testResults.isValidEmail }}
              </n-tag>
            </n-space>
          </div>

          <n-divider>日期格式化</n-divider>
          <div>
            <n-text strong>formatDate：</n-text>
            <n-text>{{ testResults.formattedDate }}</n-text>
          </div>

          <n-divider>数据格式化</n-divider>
          <div>
            <n-text strong>formatFileSize：</n-text>
            <n-text>{{ testResults.formattedFileSize }}</n-text>
          </div>

          <n-divider>防抖测试</n-divider>
          <div>
            <n-input
              v-model:value="debounceInput"
              placeholder="输入内容（防抖 500ms）"
              style="max-width: 300px"
            />
            <n-text v-if="debounceResult" type="success"> 防抖结果: {{ debounceResult }} </n-text>
          </div>
        </n-space>
      </n-card>

      <!-- API 兼容性测试 -->
      <n-card title="2. API 兼容性测试（设备管理）" segmented>
        <n-space vertical>
          <n-alert type="info"> 测试通过 Shared 层适配器调用 API，保持与原有接口兼容 </n-alert>

          <n-space>
            <n-button type="primary" :loading="apiLoading" @click="testDeviceApi">
              测试设备 API
            </n-button>
            <n-button type="info" :loading="apiLoading" @click="testDeviceTypeApi">
              测试设备类型 API
            </n-button>
            <n-button @click="clearApiResult">清空结果</n-button>
          </n-space>

          <n-card v-if="apiResult" :title="apiResult.title" size="small">
            <n-space vertical>
              <div>
                <n-text strong>状态：</n-text>
                <n-tag :type="apiResult.success ? 'success' : 'error'">
                  {{ apiResult.success ? '成功' : '失败' }}
                </n-tag>
              </div>
              <div>
                <n-text strong>耗时：</n-text>
                <n-text>{{ apiResult.duration }}ms</n-text>
              </div>
              <n-divider style="margin: 8px 0" />
              <n-code
                :code="JSON.stringify(apiResult.data, null, 2)"
                language="json"
                :hljs="hljs"
              />
            </n-space>
          </n-card>
        </n-space>
      </n-card>

      <!-- 对比测试 -->
      <n-card title="3. 新旧 API 对比" segmented>
        <n-space vertical>
          <n-alert type="warning"> 对比使用旧 API 和 Shared API 的性能与结果 </n-alert>

          <n-button type="primary" :loading="comparisonLoading" @click="runComparison">
            运行对比测试
          </n-button>

          <n-table v-if="comparisonResults.length" :bordered="false" :single-line="false">
            <thead>
              <tr>
                <th>测试项</th>
                <th>旧 API</th>
                <th>Shared API</th>
                <th>差异</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in comparisonResults" :key="item.test">
                <td>{{ item.test }}</td>
                <td>{{ item.oldApi }}</td>
                <td>{{ item.sharedApi }}</td>
                <td>
                  <n-tag :type="item.passed ? 'success' : 'error'">
                    {{ item.passed ? '✓ 一致' : '✗ 不一致' }}
                  </n-tag>
                </td>
              </tr>
            </tbody>
          </n-table>
        </n-space>
      </n-card>

      <!-- 迁移清单 -->
      <n-card title="4. 迁移进度" segmented>
        <n-space vertical>
          <n-progress
            type="line"
            :percentage="migrationProgress"
            :status="migrationProgress === 100 ? 'success' : 'default'"
          />

          <n-list bordered>
            <n-list-item v-for="item in migrationChecklist" :key="item.name">
              <template #prefix>
                <n-icon :color="item.status === 'completed' ? '#18a058' : '#808080'">
                  <span v-if="item.status === 'completed'">✓</span>
                  <span v-else>○</span>
                </n-icon>
              </template>
              <n-thing :title="item.name" :description="item.description" />
            </n-list-item>
          </n-list>
        </n-space>
      </n-card>
    </n-space>
  </CommonPage>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  NSpace,
  NCard,
  NButton,
  NAlert,
  NText,
  NTag,
  NDivider,
  NInput,
  NCode,
  NProgress,
  NList,
  NListItem,
  NThing,
  NIcon,
  NTable,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import hljs from 'highlight.js/lib/core'
import json from 'highlight.js/lib/languages/json'

// 导入工具函数（现在来自 Shared 层）
import { isEmpty, isValidEmail, formatDate, formatFileSize, debounce } from '@/utils'

// 导入 Shared API
import sharedApi from '@/api/shared'

// 导入兼容适配器
import { deviceApi, deviceTypeApi } from '@/api/device-shared'

hljs.registerLanguage('json', json)

defineOptions({ name: 'SharedMigrationTest' })

// ========== 工具函数测试 ==========

const testResults = ref({
  isEmpty: isEmpty([]),
  isValidEmail: isValidEmail('test@example.com'),
  formattedDate: formatDate(new Date()),
  formattedFileSize: formatFileSize(1024 * 1024 * 5),
})

const debounceInput = ref('')
const debounceResult = ref('')

const handleDebounceInput = debounce((value) => {
  debounceResult.value = `"${value}" (${new Date().toLocaleTimeString()})`
}, 500)

watch(debounceInput, (value) => {
  if (value) {
    handleDebounceInput(value)
  }
})

// ========== API 测试 ==========

const apiLoading = ref(false)
const apiResult = ref(null)

async function testDeviceApi() {
  apiLoading.value = true
  const startTime = Date.now()

  try {
    // 使用兼容适配器调用
    const result = await deviceApi.list({ page: 1, pageSize: 5 })

    apiResult.value = {
      title: '设备列表 API',
      success: true,
      duration: Date.now() - startTime,
      data: result.data,
    }
  } catch (error) {
    apiResult.value = {
      title: '设备列表 API',
      success: false,
      duration: Date.now() - startTime,
      data: { error: error.message },
    }
  } finally {
    apiLoading.value = false
  }
}

async function testDeviceTypeApi() {
  apiLoading.value = true
  const startTime = Date.now()

  try {
    const result = await deviceTypeApi.list({ page: 1, pageSize: 5 })

    apiResult.value = {
      title: '设备类型 API',
      success: true,
      duration: Date.now() - startTime,
      data: result.data,
    }
  } catch (error) {
    apiResult.value = {
      title: '设备类型 API',
      success: false,
      duration: Date.now() - startTime,
      data: { error: error.message },
    }
  } finally {
    apiLoading.value = false
  }
}

function clearApiResult() {
  apiResult.value = null
}

// ========== 对比测试 ==========

const comparisonLoading = ref(false)
const comparisonResults = ref([])

async function runComparison() {
  comparisonLoading.value = true
  comparisonResults.value = []

  try {
    // 测试1：工具函数一致性
    const oldIsEmpty = [].length === 0 // 模拟旧实现
    const newIsEmpty = isEmpty([])
    comparisonResults.value.push({
      test: 'isEmpty([]) 结果',
      oldApi: String(oldIsEmpty),
      sharedApi: String(newIsEmpty),
      passed: oldIsEmpty === newIsEmpty,
    })

    // 测试2：日期格式化
    const date = new Date('2025-01-01 12:00:00')
    const oldFormat = '2025-01-01 12:00:00' // 假设旧格式
    const newFormat = formatDate(date, 'YYYY-MM-DD HH:mm:ss')
    comparisonResults.value.push({
      test: '日期格式化',
      oldApi: oldFormat,
      sharedApi: newFormat,
      passed: oldFormat === newFormat,
    })

    // 测试3：文件大小格式化
    const size = 1024 * 1024
    const oldSize = '1.0 MB' // 假设旧格式
    const newSize = formatFileSize(size)
    comparisonResults.value.push({
      test: 'formatFileSize(1MB)',
      oldApi: oldSize,
      sharedApi: newSize,
      passed: oldSize === newSize,
    })

    // 测试4：Email 验证
    const email = 'test@example.com'
    const oldValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    const newValid = isValidEmail(email)
    comparisonResults.value.push({
      test: 'Email 验证',
      oldApi: String(oldValid),
      sharedApi: String(newValid),
      passed: oldValid === newValid,
    })
  } finally {
    comparisonLoading.value = false
  }
}

// ========== 迁移清单 ==========

const migrationChecklist = ref([
  {
    name: '工具函数迁移',
    description: '类型检查、日期格式化、防抖节流等',
    status: 'completed',
  },
  {
    name: '设备管理 API',
    description: '设备列表、详情、创建、更新、删除',
    status: 'completed',
  },
  {
    name: '告警管理 API',
    description: '告警列表、统计、确认、解决',
    status: 'pending',
  },
  {
    name: '维修记录 API',
    description: '维修记录列表、创建、更新、完成',
    status: 'pending',
  },
  {
    name: 'Pinia Store 更新',
    description: '使用 Shared Types 定义状态',
    status: 'pending',
  },
  {
    name: '组件迁移',
    description: '更新现有组件使用 Shared API',
    status: 'pending',
  },
])

const migrationProgress = computed(() => {
  const completed = migrationChecklist.value.filter((item) => item.status === 'completed').length
  return Math.round((completed / migrationChecklist.value.length) * 100)
})
</script>

<style scoped>
.n-card {
  margin-bottom: 16px;
}
</style>
