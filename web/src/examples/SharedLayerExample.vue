<template>
  <CommonPage title="Shared 层使用示例" desc="演示如何使用跨端共享的 API、工具和类型">
    <n-card title="1. API 调用示例" class="mb-4">
      <n-space vertical>
        <n-button type="primary" @click="testDeviceApi">测试设备 API</n-button>
        <n-button type="info" @click="testAlarmApi">测试告警 API</n-button>
        <n-button type="warning" @click="testRepairApi">测试维修 API</n-button>

        <n-divider />

        <n-code v-if="apiResult" :code="apiResult" language="json" />
      </n-space>
    </n-card>

    <n-card title="2. 工具函数示例" class="mb-4">
      <n-space vertical>
        <div>
          <n-text strong>日期格式化：</n-text>
          <n-text>{{ formattedDate }}</n-text>
        </div>

        <div>
          <n-text strong>文件大小格式化：</n-text>
          <n-text>{{ formattedFileSize }}</n-text>
        </div>

        <div>
          <n-text strong>Email 验证：</n-text>
          <n-space>
            <n-input v-model:value="testEmail" placeholder="输入 Email" style="width: 200px" />
            <n-tag :type="emailValid ? 'success' : 'error'">
              {{ emailValid ? '有效' : '无效' }}
            </n-tag>
          </n-space>
        </div>

        <div>
          <n-text strong>防抖搜索：</n-text>
          <n-input
            v-model:value="searchKeyword"
            placeholder="输入关键词（防抖 500ms）"
            style="width: 300px"
            @input="handleSearch"
          />
          <n-text v-if="searchResult" type="info">搜索结果: {{ searchResult }}</n-text>
        </div>
      </n-space>
    </n-card>

    <n-card title="3. 类型使用示例">
      <n-space vertical>
        <n-text>TypeScript 类型定义已从 shared 层导入，可在代码中使用。</n-text>

        <n-code :code="typeExample" language="typescript" />
      </n-space>
    </n-card>
  </CommonPage>
</template>

<script setup>
import { ref, computed } from 'vue'
import { NCard, NButton, NSpace, NDivider, NCode, NText, NInput, NTag } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'

// 导入 shared API
import sharedApi from '@/api/shared'

// 导入 shared 工具函数
import { formatDate, formatFileSize, isValidEmail, debounce } from '@/utils/shared'

// 导入 shared 类型（在 <script setup lang="ts"> 中使用）
// import type { Device, Alarm, User } from '@/types/shared';

defineOptions({ name: 'SharedLayerExample' })

// ========== API 示例 ==========

const apiResult = ref('')

async function testDeviceApi() {
  try {
    apiResult.value = '加载中...'
    const result = await sharedApi.device.getDevices({ page: 1, pageSize: 5 })
    apiResult.value = JSON.stringify(result, null, 2)
  } catch (error) {
    apiResult.value = `错误: ${error.message}`
  }
}

async function testAlarmApi() {
  try {
    apiResult.value = '加载中...'
    const result = await sharedApi.alarm.getAlarmStats()
    apiResult.value = JSON.stringify(result, null, 2)
  } catch (error) {
    apiResult.value = `错误: ${error.message}`
  }
}

async function testRepairApi() {
  try {
    apiResult.value = '加载中...'
    const result = await sharedApi.repair.getRepairRecords({ page: 1, pageSize: 5 })
    apiResult.value = JSON.stringify(result, null, 2)
  } catch (error) {
    apiResult.value = `错误: ${error.message}`
  }
}

// ========== 工具函数示例 ==========

const formattedDate = computed(() => {
  return formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss')
})

const formattedFileSize = computed(() => {
  return formatFileSize(1024 * 1024 * 5.5) // 5.5 MB
})

const testEmail = ref('user@example.com')
const emailValid = computed(() => {
  return isValidEmail(testEmail.value)
})

const searchKeyword = ref('')
const searchResult = ref('')

const handleSearch = debounce((value) => {
  searchResult.value = `搜索 "${value}" 完成（${new Date().toLocaleTimeString()})`
}, 500)

// ========== 类型示例 ==========

const typeExample = `import type { User, Device, Paginated } from '@/types/shared';

// 使用类型定义
const user: User = {
  id: 1,
  username: 'admin',
  nickname: '管理员',
  status: 'active',
};

const device: Device = {
  id: 1,
  device_name: '焊机-001',
  device_code: 'WM-001',
  device_type: 'welding',
  status: 'online',
};

// 分页数据
const devices: Paginated<Device> = {
  items: [device],
  total: 1,
  page: 1,
  pageSize: 20,
};`
</script>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}
</style>
