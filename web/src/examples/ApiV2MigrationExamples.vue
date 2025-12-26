<!--
API v2迁移示例组件
展示如何将前端页面从v1 API迁移到v2 API
-->
<template>
  <div class="api-v2-migration-examples">
    <n-card title="API v2迁移示例">
      <n-tabs type="line" animated>
        <!-- 基础API调用示例 -->
        <n-tab-pane name="basic" tab="基础API调用">
          <div class="example-section">
            <h3>用户管理API示例</h3>
            <n-space vertical>
              <n-button type="primary" @click="loadUserList"> 加载用户列表 (v2) </n-button>
              <n-button type="success" @click="createUser"> 创建用户 (v2) </n-button>
              <n-button type="warning" @click="updateUser"> 更新用户 (v2) </n-button>
              <n-button type="error" @click="deleteUser"> 删除用户 (v2) </n-button>
            </n-space>

            <n-divider />

            <div v-if="userList.length > 0">
              <h4>用户列表 ({{ pagination.total }} 条记录)</h4>
              <n-data-table
                :columns="userColumns"
                :data="userList"
                :pagination="paginationConfig"
                @update:page="handlePageChange"
              />
            </div>
          </div>
        </n-tab-pane>

        <!-- 高级功能示例 -->
        <n-tab-pane name="advanced" tab="高级功能">
          <div class="example-section">
            <h3>批量操作示例</h3>
            <n-space vertical>
              <n-button type="error" @click="batchDeleteUsers"> 批量删除用户 </n-button>
              <n-button type="info" @click="searchUsers"> 高级搜索用户 </n-button>
            </n-space>

            <n-divider />

            <h3>设备管理API示例</h3>
            <n-space vertical>
              <n-button type="primary" @click="loadDeviceList"> 加载设备列表 </n-button>
              <n-button type="info" @click="getDeviceData"> 获取设备数据 </n-button>
              <n-button type="success" @click="getDeviceStatistics"> 获取设备统计 </n-button>
            </n-space>
          </div>
        </n-tab-pane>

        <!-- 权限集成示例 -->
        <n-tab-pane name="permission" tab="权限集成">
          <div class="example-section">
            <h3>权限按钮示例</h3>
            <n-space>
              <!-- 使用v2权限的按钮 -->
              <PermissionButton permission="POST /api/v2/users" type="primary" @click="createUser">
                创建用户 (v2权限)
              </PermissionButton>

              <PermissionButton
                permission="PUT /api/v2/users/{user_id}"
                type="warning"
                @click="updateUser"
              >
                更新用户 (v2权限)
              </PermissionButton>

              <PermissionButton
                permission="DELETE /api/v2/users/{user_id}"
                type="error"
                @click="deleteUser"
              >
                删除用户 (v2权限)
              </PermissionButton>

              <!-- 多权限检查 -->
              <PermissionButton
                permission="GET /api/v2/users"
                :multiple-permissions="['GET /api/v2/users', 'GET /api/v2/roles']"
                :require-all-permissions="false"
                type="info"
                @click="loadUserRoleData"
              >
                用户角色管理 (多权限)
              </PermissionButton>
            </n-space>

            <n-divider />

            <h3>权限指令示例</h3>
            <div class="permission-examples">
              <!-- v2权限指令 -->
              <div v-permission.v2="{ resource: 'users', action: 'read' }">
                <n-alert type="success" title="有用户查看权限"> 您可以查看用户信息 </n-alert>
              </div>

              <div v-permission.page="{ path: '/system/user', action: 'create' }">
                <n-alert type="info" title="有用户创建权限"> 您可以创建新用户 </n-alert>
              </div>

              <!-- 权限不足时禁用 -->
              <n-button v-permission.disable="{ resource: 'users', action: 'delete' }" type="error">
                删除用户 (权限不足时禁用)
              </n-button>

              <!-- 权限不足时隐藏 -->
              <n-button
                v-permission.hide="{ resource: 'roles', action: 'assign-permissions' }"
                type="primary"
              >
                分配角色权限 (权限不足时隐藏)
              </n-button>
            </div>
          </div>
        </n-tab-pane>

        <!-- 错误处理示例 -->
        <n-tab-pane name="error" tab="错误处理">
          <div class="example-section">
            <h3>v2错误处理示例</h3>
            <n-space vertical>
              <n-button type="error" @click="triggerValidationError"> 触发验证错误 </n-button>
              <n-button type="error" @click="triggerAuthError"> 触发认证错误 </n-button>
              <n-button type="error" @click="triggerServerError"> 触发服务器错误 </n-button>
            </n-space>

            <div v-if="lastError" class="error-display">
              <n-alert type="error" :title="`错误 ${lastError.code}`">
                <div>
                  <p><strong>消息:</strong> {{ lastError.message }}</p>
                  <p v-if="lastError.error_code">
                    <strong>错误代码:</strong> {{ lastError.error_code }}
                  </p>
                  <div v-if="lastError.validation_errors">
                    <strong>验证错误:</strong>
                    <ul>
                      <li v-for="error in lastError.validation_errors" :key="error.field">
                        {{ error.field }}: {{ error.message }}
                      </li>
                    </ul>
                  </div>
                  <p v-if="lastError.help_url">
                    <strong>帮助文档:</strong>
                    <n-button text type="primary" @click="openHelpUrl(lastError.help_url)">
                      查看文档
                    </n-button>
                  </p>
                </div>
              </n-alert>
            </div>
          </div>
        </n-tab-pane>

        <!-- 迁移对比示例 -->
        <n-tab-pane name="comparison" tab="迁移对比">
          <div class="example-section">
            <h3>v1 vs v2 API对比</h3>

            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-card title="v1 API调用方式" size="small">
                  <n-code language="javascript" :code="v1CodeExample" />
                </n-card>
              </n-grid-item>

              <n-grid-item>
                <n-card title="v2 API调用方式" size="small">
                  <n-code language="javascript" :code="v2CodeExample" />
                </n-card>
              </n-grid-item>
            </n-grid>

            <n-divider />

            <h3>响应格式对比</h3>

            <n-grid :cols="2" :x-gap="16">
              <n-grid-item>
                <n-card title="v1 响应格式" size="small">
                  <n-code language="json" :code="v1ResponseExample" />
                </n-card>
              </n-grid-item>

              <n-grid-item>
                <n-card title="v2 响应格式" size="small">
                  <n-code language="json" :code="v2ResponseExample" />
                </n-card>
              </n-grid-item>
            </n-grid>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import {
  NCard,
  NTabs,
  NTabPane,
  NButton,
  NSpace,
  NDivider,
  NDataTable,
  NAlert,
  NGrid,
  NGridItem,
  NCode,
  useMessage,
} from 'naive-ui'
import PermissionButton from '@/components/common/PermissionButton.vue'
import { createSystemApis, createDeviceApis } from '@/utils/api-v2-migration'

const message = useMessage()

// 创建API实例
const systemApis = createSystemApis()
const deviceApis = createDeviceApis()

// 响应式数据
const userList = ref([])
const deviceList = ref([])
const lastError = ref(null)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 表格配置
const userColumns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '用户名', key: 'username' },
  { title: '邮箱', key: 'email' },
  { title: '状态', key: 'status' },
  { title: '创建时间', key: 'created_at' },
]

const paginationConfig = computed(() => ({
  page: pagination.page,
  pageSize: pagination.pageSize,
  itemCount: pagination.total,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
}))

// API调用方法
const loadUserList = async () => {
  try {
    const response = await systemApis.users.list({
      page: pagination.page,
      pageSize: pagination.pageSize,
    })

    userList.value = response.data || []
    pagination.total = response.total || 0

    message.success(`加载了 ${userList.value.length} 条用户记录`)
  } catch (error) {
    lastError.value = error
    message.error(`加载用户列表失败: ${error.message}`)
  }
}

const createUser = async () => {
  try {
    const userData = {
      username: `user_${Date.now()}`,
      email: `user${Date.now()}@example.com`,
      password: 'password123',
      real_name: '测试用户',
    }

    const response = await systemApis.users.create(userData)
    message.success('用户创建成功')

    // 重新加载列表
    await loadUserList()
  } catch (error) {
    lastError.value = error
    message.error(`创建用户失败: ${error.message}`)
  }
}

const updateUser = async () => {
  if (userList.value.length === 0) {
    message.warning('请先加载用户列表')
    return
  }

  try {
    const user = userList.value[0]
    const response = await systemApis.users.update(user.id, {
      real_name: `更新的用户_${Date.now()}`,
    })

    message.success('用户更新成功')
    await loadUserList()
  } catch (error) {
    lastError.value = error
    message.error(`更新用户失败: ${error.message}`)
  }
}

const deleteUser = async () => {
  if (userList.value.length === 0) {
    message.warning('请先加载用户列表')
    return
  }

  try {
    const user = userList.value[userList.value.length - 1]
    await systemApis.users.delete(user.id)

    message.success('用户删除成功')
    await loadUserList()
  } catch (error) {
    lastError.value = error
    message.error(`删除用户失败: ${error.message}`)
  }
}

const batchDeleteUsers = async () => {
  if (userList.value.length < 2) {
    message.warning('需要至少2个用户才能演示批量删除')
    return
  }

  try {
    const userIds = userList.value.slice(-2).map((user) => user.id)
    await systemApis.users.batchDelete(userIds)

    message.success('批量删除成功')
    await loadUserList()
  } catch (error) {
    lastError.value = error
    message.error(`批量删除失败: ${error.message}`)
  }
}

const searchUsers = async () => {
  try {
    const response = await systemApis.users.search({
      search: 'test',
      status: 'active',
      page: 1,
      pageSize: 10,
    })

    userList.value = response.data || []
    pagination.total = response.total || 0

    message.success(`搜索到 ${userList.value.length} 条用户记录`)
  } catch (error) {
    lastError.value = error
    message.error(`搜索用户失败: ${error.message}`)
  }
}

const loadDeviceList = async () => {
  try {
    const response = await deviceApis.devices.list({
      page: 1,
      pageSize: 20,
    })

    deviceList.value = response.data || []
    message.success(`加载了 ${deviceList.value.length} 条设备记录`)
  } catch (error) {
    lastError.value = error
    message.error(`加载设备列表失败: ${error.message}`)
  }
}

const getDeviceData = async () => {
  if (deviceList.value.length === 0) {
    message.warning('请先加载设备列表')
    return
  }

  try {
    const device = deviceList.value[0]
    const response = await deviceApis.devices.getData(device.id)

    message.success('获取设备数据成功')
  } catch (error) {
    lastError.value = error
    message.error(`获取设备数据失败: ${error.message}`)
  }
}

const getDeviceStatistics = async () => {
  try {
    const response = await deviceApis.devices.getStatistics()
    message.success('获取设备统计成功')
  } catch (error) {
    lastError.value = error
    message.error(`获取设备统计失败: ${error.message}`)
  }
}

const loadUserRoleData = async () => {
  try {
    const [usersResponse, rolesResponse] = await Promise.all([
      systemApis.users.list({ page: 1, pageSize: 5 }),
      systemApis.roles.list({ page: 1, pageSize: 5 }),
    ])

    message.success('加载用户角色数据成功')
  } catch (error) {
    lastError.value = error
    message.error(`加载用户角色数据失败: ${error.message}`)
  }
}

// 错误处理示例
const triggerValidationError = async () => {
  try {
    await systemApis.users.create({
      // 缺少必填字段，触发验证错误
      username: '',
    })
  } catch (error) {
    lastError.value = error
  }
}

const triggerAuthError = async () => {
  try {
    // 模拟认证错误
    throw {
      code: 401,
      message: 'Unauthorized',
      details: {
        error_code: 'AUTHENTICATION_ERROR',
        help_url: 'https://docs.example.com/auth',
      },
    }
  } catch (error) {
    lastError.value = error
  }
}

const triggerServerError = async () => {
  try {
    // 模拟服务器错误
    throw {
      code: 500,
      message: 'Internal Server Error',
      details: {
        error_code: 'INTERNAL_ERROR',
        help_url: 'https://docs.example.com/errors',
      },
    }
  } catch (error) {
    lastError.value = error
  }
}

const openHelpUrl = (url) => {
  window.open(url, '_blank')
}

const handlePageChange = (page) => {
  pagination.page = page
  loadUserList()
}

// 代码示例
const v1CodeExample = `// v1 API调用方式
import { request } from '@/utils/http'

// 获取用户列表
const getUserList = async (params) => {
  const response = await request.get('/user/list', { params })
  if (response.code === 200) {
    return response.data
  }
  throw new Error(response.msg)
}

// 创建用户
const createUser = async (userData) => {
  const response = await request.post('/user/create', userData)
  if (response.code === 200) {
    return response.data
  }
  throw new Error(response.msg)
}`

const v2CodeExample = `// v2 API调用方式
import { createSystemApis } from '@/utils/api-v2-migration'

const systemApis = createSystemApis()

// 获取用户列表
const getUserList = async (params) => {
  const response = await systemApis.users.list(params)
  return response.data
}

// 创建用户
const createUser = async (userData) => {
  const response = await systemApis.users.create(userData)
  return response.data
}

// 批量操作
const batchDeleteUsers = async (userIds) => {
  return await systemApis.users.batchDelete(userIds)
}

// 高级搜索
const searchUsers = async (searchParams) => {
  return await systemApis.users.search(searchParams)
}`

const v1ResponseExample = `{
  "code": 200,
  "msg": "success",
  "data": [
    { "id": 1, "name": "user1" }
  ],
  "total": 100,
  "page_num": 1,
  "page_size": 20
}`

const v2ResponseExample = `{
  "success": true,
  "code": 200,
  "message": "success",
  "data": [
    { "id": 1, "name": "user1" }
  ],
  "meta": {
    "version": "v2",
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "hasNext": true,
    "hasPrev": false,
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "req-123456",
    "executionTime": 150
  },
  "links": {
    "self": "/api/v2/users?page=1",
    "next": "/api/v2/users?page=2",
    "first": "/api/v2/users?page=1",
    "last": "/api/v2/users?page=5"
  }
}`
</script>

<style scoped>
.api-v2-migration-examples {
  padding: 20px;
}

.example-section {
  padding: 16px 0;
}

.permission-examples {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error-display {
  margin-top: 16px;
}

.n-code {
  max-height: 300px;
  overflow-y: auto;
}
</style>
