<template>
  <div class="mock-data-container">
    <n-card title="Mock数据管理" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-tag :type="mockEnabled ? 'success' : 'default'">
            {{ mockEnabled ? 'Mock已启用' : 'Mock已禁用' }}
          </n-tag>
          <n-button
            :type="mockEnabled ? 'warning' : 'primary'"
            @click="toggleMockGlobal"
          >
            {{ mockEnabled ? '禁用Mock' : '启用Mock' }}
          </n-button>
          <n-button type="primary" @click="handleAdd">
            <template #icon>
              <n-icon><AddIcon /></n-icon>
            </template>
            添加规则
          </n-button>
          <n-button @click="handleReload">
            <template #icon>
              <n-icon><RefreshIcon /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>

      <!-- 搜索区域 -->
      <n-space vertical :size="16">
        <n-space>
          <n-input
            v-model:value="searchText"
            placeholder="搜索URL或名称"
            clearable
            style="width: 300px"
          >
            <template #prefix>
              <n-icon><SearchIcon /></n-icon>
            </template>
          </n-input>
          <n-select
            v-model:value="searchMethod"
            :options="methodOptions"
            placeholder="请求方法"
            clearable
            style="width: 120px"
          />
          <n-select
            v-model:value="searchEnabled"
            :options="enabledOptions"
            placeholder="启用状态"
            clearable
            style="width: 120px"
          />
        </n-space>

        <!-- 数据表格 -->
        <n-data-table
          :columns="columns"
          :data="filteredData"
          :loading="loading"
          :pagination="pagination"
          :bordered="false"
        />
      </n-space>
    </n-card>

    <!-- 添加/编辑对话框 -->
    <n-modal
      v-model:show="showModal"
      :title="modalTitle"
      preset="card"
      style="width: 800px"
      :mask-closable="false"
    >
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="100"
      >
        <n-form-item label="规则名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入规则名称" />
        </n-form-item>

        <n-form-item label="URL匹配" path="url_pattern">
          <n-input
            v-model:value="formData.url_pattern"
            placeholder="支持正则表达式，如: /api/v2/users.*"
          />
        </n-form-item>

        <n-form-item label="请求方法" path="method">
          <n-select
            v-model:value="formData.method"
            :options="methodOptions"
            placeholder="请选择请求方法"
          />
        </n-form-item>

        <n-form-item label="响应状态码" path="response_status">
          <n-input-number
            v-model:value="formData.response_status"
            :min="100"
            :max="599"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="响应数据" path="response_data">
          <n-input
            v-model:value="formData.response_data"
            type="textarea"
            placeholder="请输入JSON格式的响应数据"
            :rows="8"
          />
        </n-form-item>

        <n-form-item label="延迟时间(ms)" path="delay">
          <n-input-number
            v-model:value="formData.delay"
            :min="0"
            :max="10000"
            style="width: 100%"
            placeholder="模拟网络延迟"
          />
        </n-form-item>

        <n-form-item label="优先级" path="priority">
          <n-input-number
            v-model:value="formData.priority"
            :min="0"
            :max="100"
            style="width: 100%"
          />
          <template #feedback>
            数字越大优先级越高
          </template>
        </n-form-item>

        <n-form-item label="是否启用" path="enabled">
          <n-switch v-model:value="formData.enabled" />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="规则描述（可选）"
            :rows="3"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { NButton, NSpace, NSwitch, NTag, useMessage, useDialog } from 'naive-ui'
import { Add as AddIcon, Refresh as RefreshIcon, Search as SearchIcon } from '@vicons/ionicons5'
import { requestV2 } from '@/utils/http/v2-interceptors'

const message = useMessage()
const dialog = useDialog()

// 状态管理
const loading = ref(false)
const showModal = ref(false)
const modalTitle = ref('添加Mock规则')
const mockEnabled = ref(false)
const dataList = ref([])
const formRef = ref(null)

// 搜索条件
const searchText = ref('')
const searchMethod = ref(null)
const searchEnabled = ref(null)

// 表单数据
const formData = ref({
  name: '',
  url_pattern: '',
  method: 'GET',
  response_status: 200,
  response_data: '{}',
  delay: 0,
  priority: 0,
  enabled: true,
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' }
  ],
  url_pattern: [
    { required: true, message: '请输入URL匹配规则', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  response_status: [
    { required: true, message: '请输入响应状态码', trigger: 'blur', type: 'number' }
  ],
  response_data: [
    { required: true, message: '请输入响应数据', trigger: 'blur' },
    {
      validator: (rule, value) => {
        try {
          JSON.parse(value)
          return true
        } catch (e) {
          return false
        }
      },
      message: '响应数据必须是有效的JSON格式',
      trigger: 'blur'
    }
  ]
}

// 下拉选项
const methodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'PATCH', value: 'PATCH' }
]

const enabledOptions = [
  { label: '已启用', value: true },
  { label: '已禁用', value: false }
]

// 分页配置
const pagination = ref({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  prefix: (info) => `共 ${info.itemCount} 条`
})

// 表格列配置
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
    align: 'center'
  },
  {
    title: '规则名称',
    key: 'name',
    width: 150,
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: 'URL匹配',
    key: 'url_pattern',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '方法',
    key: 'method',
    width: 80,
    align: 'center',
    render: (row) => {
      const typeMap = {
        GET: 'info',
        POST: 'success',
        PUT: 'warning',
        DELETE: 'error',
        PATCH: 'default'
      }
      return h(NTag, { type: typeMap[row.method] || 'default', size: 'small' }, { default: () => row.method })
    }
  },
  {
    title: '状态码',
    key: 'response_status',
    width: 80,
    align: 'center'
  },
  {
    title: '延迟(ms)',
    key: 'delay',
    width: 90,
    align: 'center'
  },
  {
    title: '优先级',
    key: 'priority',
    width: 80,
    align: 'center'
  },
  {
    title: '命中次数',
    key: 'hit_count',
    width: 90,
    align: 'center'
  },
  {
    title: '状态',
    key: 'enabled',
    width: 100,
    align: 'center',
    render: (row) => {
      return h(NSwitch, {
        value: row.enabled,
        onUpdateValue: () => handleToggleStatus(row)
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center',
    render: (row) => {
      return h(
        NSpace,
        { justify: 'center' },
        {
          default: () => [
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                text: true,
                onClick: () => handleEdit(row)
              },
              { default: () => '编辑' }
            ),
            h(
              NButton,
              {
                size: 'small',
                type: 'error',
                text: true,
                onClick: () => handleDelete(row)
              },
              { default: () => '删除' }
            ),
            h(
              NButton,
              {
                size: 'small',
                type: 'info',
                text: true,
                onClick: () => handleTest(row)
              },
              { default: () => '测试' }
            )
          ]
        }
      )
    }
  }
]

// 过滤后的数据
const filteredData = computed(() => {
  let result = dataList.value

  if (searchText.value) {
    const text = searchText.value.toLowerCase()
    result = result.filter(
      item =>
        item.name.toLowerCase().includes(text) ||
        item.url_pattern.toLowerCase().includes(text)
    )
  }

  if (searchMethod.value) {
    result = result.filter(item => item.method === searchMethod.value)
  }

  if (searchEnabled.value !== null) {
    result = result.filter(item => item.enabled === searchEnabled.value)
  }

  return result
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const response = await requestV2.get('/mock-data')
    console.log('📦 Mock数据API响应:', response)
    
    // 修复：API返回的response已经是解析后的对象，不需要再访问response.data
    if (response.success) {
      dataList.value = response.data.items || []
      console.log('✅ 加载Mock规则成功:', dataList.value.length, '条')
    } else {
      message.error(response.message || '加载数据失败')
    }
  } catch (error) {
    console.error('加载Mock规则失败:', error)
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 全局启用/禁用Mock
const toggleMockGlobal = () => {
  if (window.__mockInterceptor) {
    window.__mockInterceptor.toggle()
    mockEnabled.value = !mockEnabled.value
    message.success(mockEnabled.value ? 'Mock已启用' : 'Mock已禁用')
  } else {
    message.error('Mock拦截器未初始化')
  }
}

// 检查Mock状态
const checkMockStatus = () => {
  if (window.__mockInterceptor) {
    const stats = window.__mockInterceptor.getStats()
    mockEnabled.value = stats.enabled
  }
}

// 添加规则
const handleAdd = () => {
  modalTitle.value = '添加Mock规则'
  formData.value = {
    name: '',
    url_pattern: '',
    method: 'GET',
    response_status: 200,
    response_data: '{\n  "success": true,\n  "code": 200,\n  "message": "操作成功",\n  "data": {}\n}',
    delay: 0,
    priority: 0,
    enabled: true,
    description: ''
  }
  showModal.value = true
}

// 编辑规则
const handleEdit = (row) => {
  modalTitle.value = '编辑Mock规则'
  formData.value = {
    id: row.id,
    name: row.name,
    url_pattern: row.url_pattern,
    method: row.method,
    response_status: row.response_status,
    response_data: JSON.stringify(JSON.parse(row.response_data), null, 2),
    delay: row.delay,
    priority: row.priority,
    enabled: row.enabled,
    description: row.description || ''
  }
  showModal.value = true
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    
    loading.value = true
    const data = {
      ...formData.value,
      response_data: JSON.stringify(JSON.parse(formData.value.response_data))
    }

    let response
    if (data.id) {
      response = await requestV2.put(`/mock-data/${data.id}`, data)
    } else {
      response = await requestV2.post('/mock-data', data)
    }

    if (response.data.success) {
      message.success(data.id ? '更新成功' : '添加成功')
      showModal.value = false
      await loadData()
      // 重新加载Mock规则
      if (window.__mockInterceptor) {
        await window.__mockInterceptor.reload()
      }
    } else {
      message.error(response.data.message || '操作失败')
    }
  } catch (error) {
    if (error instanceof Error && error.message) {
      // 验证错误
      return
    }
    console.error('提交失败:', error)
    message.error('操作失败')
  } finally {
    loading.value = false
  }
}

// 切换启用状态
const handleToggleStatus = async (row) => {
  try {
    const response = await requestV2.post(`/mock-data/${row.id}/toggle`, {
      enabled: !row.enabled
    })
    if (response.data.success) {
      message.success('状态更新成功')
      await loadData()
      // 重新加载Mock规则
      if (window.__mockInterceptor) {
        await window.__mockInterceptor.reload()
      }
    } else {
      message.error(response.data.message || '操作失败')
    }
  } catch (error) {
    console.error('切换状态失败:', error)
    message.error('操作失败')
  }
}

// 删除规则
const handleDelete = (row) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除规则 "${row.name}" 吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const response = await requestV2.delete(`/mock-data/${row.id}`)
        if (response.data.success) {
          message.success('删除成功')
          await loadData()
          // 重新加载Mock规则
          if (window.__mockInterceptor) {
            await window.__mockInterceptor.reload()
          }
        } else {
          message.error(response.data.message || '删除失败')
        }
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

// 测试规则
const handleTest = (row) => {
  dialog.info({
    title: `测试Mock规则: ${row.name}`,
    content: () => {
      return h('div', [
        h('p', `URL匹配: ${row.url_pattern}`),
        h('p', `请求方法: ${row.method}`),
        h('p', `响应状态码: ${row.response_status}`),
        h('p', `延迟: ${row.delay}ms`),
        h('div', { style: 'margin-top: 10px' }, [
          h('strong', '响应数据:'),
          h('pre', {
            style: 'background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto; max-height: 300px'
          }, JSON.stringify(JSON.parse(row.response_data), null, 2))
        ])
      ])
    },
    positiveText: '关闭'
  })
}

// 刷新
const handleReload = async () => {
  await loadData()
  if (window.__mockInterceptor) {
    await window.__mockInterceptor.reload()
    message.success('规则已刷新')
  }
}

// 初始化
onMounted(() => {
  loadData()
  checkMockStatus()
})
</script>

<style scoped>
.mock-data-container {
  padding: 16px;
}

:deep(.n-data-table) {
  font-size: 14px;
}

:deep(.n-card__header) {
  padding: 16px;
}

:deep(.n-card__content) {
  padding: 16px;
}
</style>

