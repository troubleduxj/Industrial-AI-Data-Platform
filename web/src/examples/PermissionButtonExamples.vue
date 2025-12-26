<template>
  <div class="permission-examples">
    <h2>权限按钮设置示例</h2>

    <!-- 1. API权限控制 -->
    <n-card title="1. API权限控制" class="mb-4">
      <n-space>
        <!-- 基于具体API端点的权限控制 -->
        <PermissionButton permission="GET /api/v2/users" @click="viewUsers">
          查看用户
        </PermissionButton>

        <PermissionButton permission="POST /api/v2/users" type="primary" @click="createUser">
          创建用户
        </PermissionButton>

        <PermissionButton permission="DELETE /api/v2/users/{id}" type="error" @click="deleteUser">
          删除用户
        </PermissionButton>
      </n-space>

      <n-divider />

      <!-- 多个权限（任一权限） -->
      <PermissionButton
        :permission="['GET /api/v2/users', 'POST /api/v2/users']"
        permission-mode="any"
        @click="userOperations"
      >
        用户操作（任一权限）
      </PermissionButton>

      <!-- 多个权限（所有权限） -->
      <PermissionButton
        :permission="['GET /api/v2/users', 'PUT /api/v2/users/{id}']"
        permission-mode="all"
        @click="fullUserAccess"
      >
        完整用户权限（需要所有权限）
      </PermissionButton>
    </n-card>

    <!-- 2. 按钮级权限控制 -->
    <n-card title="2. 按钮级权限控制（推荐）" class="mb-4">
      <n-space>
        <!-- 基于API权限的权限控制 -->
        <PermissionButton permission="POST /api/v2/users" type="primary" @click="createUser">
          创建用户
        </PermissionButton>

        <PermissionButton permission="GET /api/v2/users" @click="viewUsers">
          查看用户
        </PermissionButton>

        <PermissionButton permission="PUT /api/v2/users/{user_id}" @click="updateUser">
          更新用户
        </PermissionButton>

        <PermissionButton
          permission="DELETE /api/v2/users/{user_id}"
          type="error"
          @click="deleteUser"
        >
          删除用户
        </PermissionButton>

        <PermissionButton permission="GET /api/v2/users/export" @click="exportUsers">
          导出用户
        </PermissionButton>
      </n-space>

      <n-divider />

      <!-- 设备管理权限 -->
      <n-space>
        <PermissionButton
          permission="PUT /api/v2/devices/{device_id}/control"
          type="warning"
          @click="controlDevice"
        >
          设备控制
        </PermissionButton>

        <PermissionButton
          permission="GET /api/v2/devices/{device_id}/monitor"
          @click="monitorDevice"
        >
          设备监控
        </PermissionButton>

        <PermissionButton permission="PUT /api/v2/devices/{device_id}/config" @click="configDevice">
          设备配置
        </PermissionButton>
      </n-space>

      <n-divider />

      <!-- AI监控权限 -->
      <n-space>
        <PermissionButton
          permission="POST /api/v2/ai-monitor/predictions"
          type="primary"
          @click="startPrediction"
        >
          开始预测
        </PermissionButton>

        <PermissionButton permission="POST /api/v2/ai-monitor/models/train" @click="trainModel">
          训练模型
        </PermissionButton>

        <PermissionButton permission="GET /api/v2/ai-monitor/reports/export" @click="exportReport">
          导出报告
        </PermissionButton>
      </n-space>
    </n-card>

    <!-- 3. 角色权限控制 -->
    <n-card title="3. 角色权限控制" class="mb-4">
      <n-space>
        <!-- 单个角色 -->
        <PermissionButton
          permission="POST /api/v2/admin/functions"
          roles="admin"
          type="error"
          @click="adminFunction"
        >
          管理员功能
        </PermissionButton>

        <PermissionButton
          permission="GET /api/v2/manager/functions"
          roles="manager"
          @click="managerFunction"
        >
          管理员功能
        </PermissionButton>

        <!-- 多个角色（任一角色） -->
        <PermissionButton
          permission="GET /api/v2/management/functions"
          :roles="['admin', 'manager']"
          permission-mode="any"
          @click="managementFunction"
        >
          管理功能（任一角色）
        </PermissionButton>

        <!-- 多个角色（所有角色） -->
        <PermissionButton
          permission="POST /api/v2/super-admin/functions"
          :roles="['admin', 'super_user']"
          permission-mode="all"
          @click="superAdminFunction"
        >
          超级管理员功能（需要所有角色）
        </PermissionButton>
      </n-space>
    </n-card>

    <!-- 4. 权限行为配置 -->
    <n-card title="4. 权限行为配置" class="mb-4">
      <n-space vertical>
        <!-- 默认行为：隐藏按钮 -->
        <div>
          <n-text>默认行为（隐藏按钮）：</n-text>
          <PermissionButton
            permission="FAKE_PERMISSION"
            :hide-when-no-permission="true"
            @click="fakeAction"
          >
            无权限时隐藏
          </PermissionButton>
        </div>

        <!-- 禁用按钮 -->
        <div>
          <n-text>禁用按钮：</n-text>
          <PermissionButton
            permission="FAKE_PERMISSION"
            :hide-when-no-permission="false"
            :disable-when-no-permission="true"
            @click="fakeAction"
          >
            无权限时禁用
          </PermissionButton>
        </div>
      </n-space>
    </n-card>

    <!-- 5. 复杂权限组合 -->
    <n-card title="5. 复杂权限组合" class="mb-4">
      <n-space>
        <!-- 同时检查API权限和角色 -->
        <PermissionButton
          permission="PUT /api/v2/users/{id}"
          roles="admin"
          @click="adminUserUpdate"
        >
          管理员用户更新
        </PermissionButton>

        <!-- 按钮权限 + 角色权限 -->
        <PermissionButton
          permission="GET /api/v2/system/params"
          roles="super_admin"
          @click="systemParam"
        >
          系统参数
        </PermissionButton>
      </n-space>
    </n-card>

    <!-- 6. 动态权限配置 -->
    <n-card title="6. 动态权限配置" class="mb-4">
      <n-space vertical>
        <n-space>
          <n-select
            v-model:value="selectedResource"
            :options="resourceOptions"
            placeholder="选择资源"
            style="width: 150px"
          />
          <n-select
            v-model:value="selectedAction"
            :options="actionOptions"
            placeholder="选择操作"
            style="width: 150px"
          />
        </n-space>

        <PermissionButton
          :permission="getDynamicPermission(selectedResource, selectedAction)"
          :disabled="!selectedResource || !selectedAction"
          @click="dynamicAction"
        >
          动态权限按钮
        </PermissionButton>
      </n-space>
    </n-card>

    <!-- 7. 权限状态显示 -->
    <n-card title="7. 权限状态显示" class="mb-4">
      <n-space vertical>
        <div>
          <n-text>当前用户权限状态：</n-text>
          <n-tag v-for="permission in userPermissions" :key="permission" class="mr-2">
            {{ permission }}
          </n-tag>
        </div>

        <div>
          <n-text>当前用户角色：</n-text>
          <n-tag v-for="role in userRoles" :key="role" type="info" class="mr-2">
            {{ role }}
          </n-tag>
        </div>

        <n-space>
          <n-button @click="refreshPermissions">刷新权限</n-button>
          <n-button @click="simulatePermissionChange">模拟权限变化</n-button>
        </n-space>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import PermissionButton from '@/components/common/PermissionButton.vue'
import { usePermission } from '@/composables/usePermission'

const message = useMessage()
const { permissions, roles } = usePermission()

// 动态权限配置
const selectedResource = ref('')
const selectedAction = ref('')

const resourceOptions = [
  { label: '用户', value: 'user' },
  { label: '角色', value: 'role' },
  { label: '设备', value: 'device' },
  { label: '报警', value: 'alarm' },
  { label: 'AI监控', value: 'ai-monitor' },
  { label: '系统', value: 'system' },
]

const actionOptions = [
  { label: '创建', value: 'create' },
  { label: '读取', value: 'read' },
  { label: '更新', value: 'update' },
  { label: '删除', value: 'delete' },
  { label: '导出', value: 'export' },
  { label: '导入', value: 'import' },
  { label: '执行', value: 'execute' },
  { label: '监控', value: 'monitor' },
  { label: '配置', value: 'config' },
]

// 用户权限和角色
const userPermissions = computed(() => permissions.value || [])
const userRoles = computed(() => roles.value?.map((role) => role.name) || [])

// 按钮点击处理函数
const viewUsers = () => message.success('查看用户列表')
const createUser = () => message.success('创建新用户')
const updateUser = () => message.success('更新用户信息')
const deleteUser = () => message.warning('删除用户')
const exportUsers = () => message.info('导出用户数据')

const controlDevice = () => message.success('设备控制操作')
const monitorDevice = () => message.info('设备监控')
const configDevice = () => message.success('设备配置')

const startPrediction = () => message.success('开始AI预测')
const trainModel = () => message.success('开始模型训练')
const exportReport = () => message.info('导出分析报告')

const adminFunction = () => message.error('执行管理员功能')
const managerFunction = () => message.warning('执行管理员功能')
const managementFunction = () => message.success('执行管理功能')
const superAdminFunction = () => message.error('执行超级管理员功能')

const adminUserUpdate = () => message.success('管理员更新用户')
const systemParam = () => message.success('系统参数管理')

const getDynamicPermission = (resource, action) => {
  if (!resource || !action) return ''

  // 根据资源和操作生成对应的API权限
  const methodMap = {
    create: 'POST',
    read: 'GET',
    update: 'PUT',
    delete: 'DELETE',
    export: 'GET',
    import: 'POST',
    execute: 'POST',
    monitor: 'GET',
    config: 'PUT',
  }

  const method = methodMap[action] || 'GET'
  const resourcePath = resource === 'ai-monitor' ? 'ai-monitor' : resource + 's'

  if (action === 'export') {
    return `${method} /api/v2/${resourcePath}/export`
  } else if (action === 'read') {
    return `${method} /api/v2/${resourcePath}`
  } else if (action === 'create') {
    return `${method} /api/v2/${resourcePath}`
  } else {
    return `${method} /api/v2/${resourcePath}/{id}`
  }
}

const dynamicAction = () => {
  message.success(`执行 ${selectedResource.value} 的 ${selectedAction.value} 操作`)
}

const fakeAction = () => message.info('这个操作不会执行（无权限）')

const refreshPermissions = () => {
  message.info('权限已刷新')
  // 这里可以调用API刷新权限
}

const simulatePermissionChange = () => {
  message.success('模拟权限变化')
  // 这里可以模拟权限变化
}

const userOperations = () => message.success('用户操作（任一权限）')
const fullUserAccess = () => message.success('完整用户权限操作')
</script>

<style scoped>
.permission-examples {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.mb-4 {
  margin-bottom: 16px;
}

.mr-2 {
  margin-right: 8px;
}
</style>
