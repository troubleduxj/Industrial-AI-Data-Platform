<template>
  <CommonPage title="组件迁移测试助手" desc="帮助验证迁移后的组件功能">
    <n-card title="测试控制台">
      <n-space vertical>
        <n-alert type="info"> 使用此工具测试迁移后的 API 是否正常工作 </n-alert>

        <n-divider>设备 API 测试</n-divider>

        <n-space>
          <n-button type="primary" :loading="loading.device" @click="testDeviceList">
            测试设备列表 API
          </n-button>
          <n-button type="info" :loading="loading.deviceType" @click="testDeviceTypeList">
            测试设备类型 API
          </n-button>
          <n-button @click="clearResults">清空结果</n-button>
        </n-space>

        <n-divider>测试结果</n-divider>

        <n-space v-if="testResults.length" vertical>
          <n-card
            v-for="(result, index) in testResults"
            :key="index"
            :title="result.title"
            size="small"
            :bordered="false"
          >
            <template #header-extra>
              <n-tag :type="result.success ? 'success' : 'error'">
                {{ result.success ? '✅ 成功' : '❌ 失败' }}
              </n-tag>
            </template>

            <n-space vertical>
              <div>
                <n-text strong>API: </n-text>
                <n-text code>{{ result.api }}</n-text>
              </div>

              <div>
                <n-text strong>耗时: </n-text>
                <n-text>{{ result.duration }}ms</n-text>
              </div>

              <div v-if="result.success">
                <n-text strong>数据量: </n-text>
                <n-text>{{ result.count }} 条记录</n-text>
              </div>

              <div v-if="!result.success">
                <n-text strong>错误信息: </n-text>
                <n-text type="error">{{ result.error }}</n-text>
              </div>

              <n-collapse>
                <n-collapse-item title="查看响应数据" name="data">
                  <n-code
                    :code="JSON.stringify(result.data, null, 2)"
                    language="json"
                    :hljs="hljs"
                  />
                </n-collapse-item>
              </n-collapse>
            </n-space>
          </n-card>
        </n-space>

        <n-empty v-else description="暂无测试结果" />
      </n-space>
    </n-card>

    <n-card title="迁移检查清单" style="margin-top: 16px">
      <n-space vertical>
        <n-checkbox-group v-model:value="checklist">
          <n-space vertical>
            <n-checkbox value="import">
              <n-text>已更新导入语句（使用 device-shared.js）</n-text>
            </n-checkbox>
            <n-checkbox value="list">
              <n-text>已替换 deviceApi.list() 调用</n-text>
            </n-checkbox>
            <n-checkbox value="create">
              <n-text>已替换 deviceApi.create() 调用</n-text>
            </n-checkbox>
            <n-checkbox value="update">
              <n-text>已替换 deviceApi.update() 调用</n-text>
            </n-checkbox>
            <n-checkbox value="delete">
              <n-text>已替换 deviceApi.delete() 调用</n-text>
            </n-checkbox>
            <n-checkbox value="console">
              <n-text>已添加控制台日志标记</n-text>
            </n-checkbox>
            <n-checkbox value="test">
              <n-text>已测试所有功能正常</n-text>
            </n-checkbox>
          </n-space>
        </n-checkbox-group>

        <n-divider />

        <n-progress
          type="line"
          :percentage="checklistProgress"
          :status="checklistProgress === 100 ? 'success' : 'default'"
        />

        <n-text v-if="checklistProgress === 100" type="success">
          ✅ 迁移完成！所有检查项已通过
        </n-text>
      </n-space>
    </n-card>
  </CommonPage>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  NCard,
  NSpace,
  NButton,
  NAlert,
  NDivider,
  NTag,
  NText,
  NCode,
  NCollapse,
  NCollapseItem,
  NEmpty,
  NCheckbox,
  NCheckboxGroup,
  NProgress,
} from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import hljs from 'highlight.js/lib/core'
import json from 'highlight.js/lib/languages/json'

// 导入 Shared API
import { deviceApi, deviceTypeApi } from '@/api/device-shared'

hljs.registerLanguage('json', json)

defineOptions({ name: 'MigrationTestHelper' })

const loading = ref({
  device: false,
  deviceType: false,
})

const testResults = ref([])

const checklist = ref([])

const checklistProgress = computed(() => {
  const total = 7 // 总共 7 个检查项
  return Math.round((checklist.value.length / total) * 100)
})

async function testDeviceList() {
  loading.value.device = true
  const startTime = performance.now()

  try {
    const result = await deviceApi.list({ page: 1, pageSize: 5 })
    const endTime = performance.now()

    const items = Array.isArray(result.data) ? result.data : result.data?.items || []

    testResults.value.unshift({
      title: '设备列表 API 测试',
      api: 'deviceApi.list()',
      success: true,
      duration: Math.round(endTime - startTime),
      count: items.length,
      data: result.data,
    })

    window.$message?.success('设备列表 API 测试成功')
  } catch (error) {
    const endTime = performance.now()

    testResults.value.unshift({
      title: '设备列表 API 测试',
      api: 'deviceApi.list()',
      success: false,
      duration: Math.round(endTime - startTime),
      error: error.message,
      data: null,
    })

    window.$message?.error(`设备列表 API 测试失败: ${error.message}`)
  } finally {
    loading.value.device = false
  }
}

async function testDeviceTypeList() {
  loading.value.deviceType = true
  const startTime = performance.now()

  try {
    const result = await deviceTypeApi.list({ page: 1, pageSize: 10 })
    const endTime = performance.now()

    const items = Array.isArray(result.data) ? result.data : result.data?.items || []

    testResults.value.unshift({
      title: '设备类型 API 测试',
      api: 'deviceTypeApi.list()',
      success: true,
      duration: Math.round(endTime - startTime),
      count: items.length,
      data: result.data,
    })

    window.$message?.success('设备类型 API 测试成功')
  } catch (error) {
    const endTime = performance.now()

    testResults.value.unshift({
      title: '设备类型 API 测试',
      api: 'deviceTypeApi.list()',
      success: false,
      duration: Math.round(endTime - startTime),
      error: error.message,
      data: null,
    })

    window.$message?.error(`设备类型 API 测试失败: ${error.message}`)
  } finally {
    loading.value.deviceType = false
  }
}

function clearResults() {
  testResults.value = []
  window.$message?.info('测试结果已清空')
}
</script>

<style scoped>
.n-card {
  margin-bottom: 16px;
}
</style>
