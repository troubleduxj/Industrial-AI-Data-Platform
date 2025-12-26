<!--
权限树形选择组件 v2
支持API v2权限格式的树形权限选择器
功能特性：
1. 支持v2权限格式
2. 权限搜索和过滤
3. 懒加载和性能优化
4. 批量操作
5. 权限统计
-->
<template>
  <div class="permission-tree-v2">
    <!-- 工具栏 -->
    <div class="toolbar mb-4">
      <n-space>
        <n-button size="small" @click="expandAll">
          <template #icon>
            <n-icon><ExpandIcon /></n-icon>
          </template>
          展开全部
        </n-button>
        <n-button size="small" @click="collapseAll">
          <template #icon>
            <n-icon><CollapseIcon /></n-icon>
          </template>
          收起全部
        </n-button>
        <n-button size="small" @click="selectAll">
          <template #icon>
            <n-icon><CheckAllIcon /></n-icon>
          </template>
          全选
        </n-button>
        <n-button size="small" @click="clearAll">
          <template #icon>
            <n-icon><ClearIcon /></n-icon>
          </template>
          清空
        </n-button>
      </n-space>

      <!-- 搜索框 -->
      <n-input
        v-model:value="searchKeyword"
        placeholder="搜索权限..."
        clearable
        class="search-input"
      >
        <template #prefix>
          <n-icon><SearchIcon /></n-icon>
        </template>
      </n-input>
    </div>

    <!-- 权限统计 -->
    <div class="permission-stats mb-4">
      <n-alert type="info" :show-icon="false">
        <template #header>
          <span>权限统计</span>
        </template>
        已选择 <strong>{{ selectedCount }}</strong> 个权限， 共
        <strong>{{ totalCount }}</strong> 个权限
        <span v-if="searchKeyword">
          （搜索结果：<strong>{{ filteredCount }}</strong> 个）
        </span>
      </n-alert>
    </div>

    <!-- 权限树 -->
    <div class="tree-container">
      <n-tree
        ref="treeRef"
        :data="filteredTreeData"
        :checked-keys="checkedKeys"
        :expanded-keys="expandedKeys"
        :pattern="searchKeyword"
        checkable
        :cascade="false"
        virtual-scroll
        block-line
        :height="treeHeight"
        :node-props="nodeProps"
        :render-label="renderLabel"
        @update:checked-keys="handleCheckedKeysChange"
        @update:expanded-keys="handleExpandedKeysChange"
      />
    </div>

    <!-- 批量操作 -->
    <div class="batch-operations mt-4">
      <n-collapse>
        <n-collapse-item title="批量操作" name="batch">
          <n-space vertical>
            <div>
              <n-text strong>按模块批量选择：</n-text>
              <n-space class="mt-2" :wrap="true">
                <n-button
                  v-for="module in moduleList"
                  :key="module.key"
                  size="small"
                  @click="selectModule(module.key)"
                >
                  <template #icon>
                    <n-icon><component :is="module.icon" /></n-icon>
                  </template>
                  {{ module.label }}
                </n-button>
              </n-space>
            </div>

            <div>
              <n-text strong>按操作类型批量选择：</n-text>
              <n-space class="mt-2" :wrap="true">
                <n-button
                  v-for="action in actionList"
                  :key="action.method"
                  size="small"
                  :type="getMethodTagType(action.method)"
                  @click="selectByMethod(action.method)"
                >
                  {{ action.label }}
                </n-button>
              </n-space>
            </div>
          </n-space>
        </n-collapse-item>
      </n-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, h } from 'vue'
import {
  NTree,
  NButton,
  NInput,
  NIcon,
  NSpace,
  NAlert,
  NTag,
  NText,
  NCollapse,
  NCollapseItem,
} from 'naive-ui'
import {
  ExpandOutline as ExpandIcon,
  ContractOutline as CollapseIcon,
  CheckmarkCircleOutline as CheckAllIcon,
  CloseCircleOutline as ClearIcon,
  SearchOutline as SearchIcon,
  FolderOutline as FolderIcon,
  DocumentOutline as ApiIcon,
  SettingsOutline as SystemIcon,
  PeopleOutline as UserIcon,
  ShieldOutline as SecurityIcon,
  HardwareChipOutline as DeviceIcon,
  AlertCircleOutline as AlarmIcon,
  BarChartOutline as StatsIcon,
  SpeedometerOutline as DashboardIcon,
  BrainOutline as AiIcon,
} from '@vicons/ionicons5'

import { getPermissionsByModule } from '@/utils/permission-config-v2'

const props = defineProps({
  // 已选中的权限标识列表
  selectedPermissions: {
    type: Array,
    default: () => [],
  },
  // 是否只读
  readonly: {
    type: Boolean,
    default: false,
  },
  // 树的高度
  treeHeight: {
    type: Number,
    default: 400,
  },
  // 是否启用懒加载
  lazy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:selectedPermissions', 'change'])

// 响应式数据
const treeRef = ref(null)
const searchKeyword = ref('')
const checkedKeys = ref([])
const expandedKeys = ref([])

// 模块配置 - 支持v2权限结构
const moduleList = [
  {
    key: 'system',
    label: '系统管理',
    icon: SystemIcon,
    resources: ['users', 'roles', 'menus', 'departments'],
  },
  {
    key: 'device',
    label: '设备管理',
    icon: DeviceIcon,
    resources: ['devices', 'device-types', 'device-maintenance', 'device-processes'],
  },
  {
    key: 'ai',
    label: 'AI监控',
    icon: AiIcon,
    resources: ['ai-predictions', 'ai-models', 'ai-annotations', 'ai-health-scores', 'ai-analysis'],
  },
  {
    key: 'monitoring',
    label: '监控管理',
    icon: AlarmIcon,
    resources: ['alarms', 'statistics', 'dashboard'],
  },
]

// 操作类型配置
const actionList = [
  { method: 'GET', label: '查询', color: '#2080f0' },
  { method: 'POST', label: '新增', color: '#18a058' },
  { method: 'PUT', label: '修改', color: '#f0a020' },
  { method: 'DELETE', label: '删除', color: '#d03050' },
]

// 获取v2权限配置
const permissionsByModule = computed(() => getPermissionsByModule())

// 构建树形数据 - 支持v2权限格式
const treeData = computed(() => {
  const modules = permissionsByModule.value

  return moduleList
    .map((moduleConfig) => {
      const modulePermissions = modules[moduleConfig.key] || {}

      const children = Object.entries(modulePermissions).map(
        ([resourceName, resourcePermissions]) => {
          // 按HTTP方法分组
          const methodGroups = {}

          Object.entries(resourcePermissions).forEach(([action, permission]) => {
            const [method] = permission.split(' ')

            if (!methodGroups[method]) {
              methodGroups[method] = {
                key: `${moduleConfig.key}_${resourceName}_${method}`,
                label: `${getMethodLabel(method)}操作`,
                type: 'method',
                method: method,
                children: [],
              }
            }

            methodGroups[method].children.push({
              key: permission, // 使用完整权限标识作为key
              label: getActionLabel(action),
              type: 'permission',
              method: method,
              action: action,
              resource: resourceName,
              permission: permission,
              description: permission,
            })
          })

          return {
            key: `${moduleConfig.key}_${resourceName}`,
            label: getResourceLabel(resourceName),
            type: 'resource',
            resource: resourceName,
            children: Object.values(methodGroups),
          }
        }
      )

      return {
        key: moduleConfig.key,
        label: moduleConfig.label,
        type: 'module',
        icon: moduleConfig.icon,
        children: children.filter((child) => child.children.length > 0),
      }
    })
    .filter((module) => module.children.length > 0)
})

// 过滤后的树形数据 - 支持搜索
const filteredTreeData = computed(() => {
  if (!searchKeyword.value) {
    return treeData.value
  }

  const keyword = searchKeyword.value.toLowerCase()

  const filterTree = (nodes) => {
    return nodes
      .map((node) => {
        const matchesKeyword =
          node.label.toLowerCase().includes(keyword) ||
          (node.description && node.description.toLowerCase().includes(keyword)) ||
          (node.permission && node.permission.toLowerCase().includes(keyword)) ||
          (node.resource && node.resource.toLowerCase().includes(keyword))

        if (node.children) {
          const filteredChildren = filterTree(node.children)
          if (filteredChildren.length > 0 || matchesKeyword) {
            return {
              ...node,
              children: filteredChildren,
            }
          }
          return null
        }

        return matchesKeyword ? node : null
      })
      .filter(Boolean)
  }

  return filterTree(treeData.value)
})

// 统计信息
const totalCount = computed(() => {
  const countPermissions = (nodes) => {
    return nodes.reduce((count, node) => {
      if (node.type === 'permission') {
        return count + 1
      }
      if (node.children) {
        return count + countPermissions(node.children)
      }
      return count
    }, 0)
  }
  return countPermissions(treeData.value)
})

const filteredCount = computed(() => {
  const countPermissions = (nodes) => {
    return nodes.reduce((count, node) => {
      if (node.type === 'permission') {
        return count + 1
      }
      if (node.children) {
        return count + countPermissions(node.children)
      }
      return count
    }, 0)
  }
  return countPermissions(filteredTreeData.value)
})

const selectedCount = computed(() => {
  return checkedKeys.value.filter((key) => key.includes('/api/v2/')).length
})

// 节点属性
const nodeProps = ({ option }) => {
  return {
    class: `tree-node-${option.type}`,
    style: {
      padding: '4px 0',
    },
  }
}

// 自定义节点渲染
const renderLabel = ({ option }) => {
  const iconComponent = getNodeIcon(option)
  const iconColor = getNodeIconColor(option)

  return h('div', { class: 'tree-node' }, [
    h(
      NIcon,
      {
        class: 'node-icon',
        color: iconColor,
      },
      {
        default: () => h(iconComponent),
      }
    ),
    h('span', { class: 'node-label' }, option.label),
    option.method &&
      h(
        NTag,
        {
          type: getMethodTagType(option.method),
          size: 'small',
          class: 'method-tag',
        },
        {
          default: () => option.method,
        }
      ),
    option.description &&
      h(
        'span',
        {
          class: 'node-description',
        },
        option.description
      ),
  ])
}

// 获取节点图标
const getNodeIcon = (option) => {
  switch (option.type) {
    case 'module':
      return option.icon || FolderIcon
    case 'resource':
      if (option.resource.includes('user')) return UserIcon
      if (option.resource.includes('device')) return DeviceIcon
      if (option.resource.includes('ai')) return AiIcon
      if (option.resource.includes('alarm')) return AlarmIcon
      if (option.resource.includes('dashboard')) return DashboardIcon
      if (option.resource.includes('statistics')) return StatsIcon
      return FolderIcon
    case 'method':
      return FolderIcon
    case 'permission':
      return ApiIcon
    default:
      return FolderIcon
  }
}

// 获取节点图标颜色
const getNodeIconColor = (option) => {
  switch (option.type) {
    case 'module':
      return '#2080f0'
    case 'resource':
      return '#18a058'
    case 'method':
      return getMethodColor(option.method)
    case 'permission':
      return getMethodColor(option.method)
    default:
      return '#666'
  }
}

// 获取方法标签类型
const getMethodTagType = (method) => {
  switch (method) {
    case 'GET':
      return 'info'
    case 'POST':
      return 'success'
    case 'PUT':
      return 'warning'
    case 'DELETE':
      return 'error'
    default:
      return 'default'
  }
}

// 获取方法颜色
const getMethodColor = (method) => {
  const action = actionList.find((a) => a.method === method)
  return action ? action.color : '#666'
}

// 获取方法标签
const getMethodLabel = (method) => {
  const action = actionList.find((a) => a.method === method)
  return action ? action.label : method
}

// 获取资源标签
const getResourceLabel = (resource) => {
  const resourceLabels = {
    users: '用户管理',
    roles: '角色管理',
    menus: '菜单管理',
    departments: '部门管理',
    devices: '设备信息',
    'device-types': '设备类型',
    'device-maintenance': '设备维护',
    'device-processes': '工艺管理',
    'ai-predictions': '趋势预测',
    'ai-models': '模型管理',
    'ai-annotations': '数据标注',
    'ai-health-scores': '健康评分',
    'ai-analysis': '智能分析',
    alarms: '报警管理',
    statistics: '统计分析',
    dashboard: '仪表板',
  }
  return resourceLabels[resource] || resource
}

// 获取操作标签
const getActionLabel = (action) => {
  const actionLabels = {
    read: '查看',
    create: '创建',
    update: '更新',
    delete: '删除',
    'reset-password': '重置密码',
    permissions: '权限管理',
    batch: '批量操作',
    search: '高级搜索',
    data: '数据查看',
    status: '状态查看',
    statistics: '统计信息',
    tree: '树形结构',
    maintenance: '维护记录',
    schedule: '维护计划',
    execute: '执行操作',
    export: '导出',
    import: '导入',
    share: '分享',
    train: '训练',
    metrics: '指标',
    results: '结果',
    handle: '处理',
    'batch-handle': '批量处理',
    acknowledge: '确认',
    'online-rate': '在线率',
    'weld-records': '焊接记录',
    'weld-time': '焊接时长',
    'welding-reports': '焊接报告',
    'custom-report': '自定义报告',
    overview: '概览',
    'device-stats': '设备统计',
    'alarm-stats': '报警统计',
    widgets: '组件管理',
    'create-widget': '创建组件',
    'update-widget': '更新组件',
    config: '配置',
    trends: '趋势',
  }
  return actionLabels[action] || action
}

// 事件处理
const handleCheckedKeysChange = (keys) => {
  checkedKeys.value = keys

  // 提取权限标识
  const permissionKeys = keys.filter((key) => key.includes('/api/v2/'))

  emit('update:selectedPermissions', permissionKeys)
  emit('change', permissionKeys)
}

const handleExpandedKeysChange = (keys) => {
  expandedKeys.value = keys
}

// 工具方法
const expandAll = () => {
  const getAllKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.type !== 'permission') {
        keys.push(node.key)
      }
      if (node.children) {
        keys.push(...getAllKeys(node.children))
      }
    })
    return keys
  }
  expandedKeys.value = getAllKeys(treeData.value)
}

const collapseAll = () => {
  expandedKeys.value = []
}

const selectAll = () => {
  const getAllPermissionKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.type === 'permission') {
        keys.push(node.key)
      }
      if (node.children) {
        keys.push(...getAllPermissionKeys(node.children))
      }
    })
    return keys
  }
  checkedKeys.value = getAllPermissionKeys(treeData.value)
}

const clearAll = () => {
  checkedKeys.value = []
}

const selectModule = (moduleKey) => {
  const getModulePermissionKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.key === moduleKey) {
        const getPermissionKeys = (children) => {
          children.forEach((child) => {
            if (child.type === 'permission') {
              keys.push(child.key)
            }
            if (child.children) {
              getPermissionKeys(child.children)
            }
          })
        }
        if (node.children) {
          getPermissionKeys(node.children)
        }
      }
    })
    return keys
  }

  const moduleKeys = getModulePermissionKeys(treeData.value)
  checkedKeys.value = [...new Set([...checkedKeys.value, ...moduleKeys])]
}

const selectByMethod = (method) => {
  const getMethodPermissionKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.type === 'permission' && node.method === method) {
        keys.push(node.key)
      }
      if (node.children) {
        keys.push(...getMethodPermissionKeys(node.children))
      }
    })
    return keys
  }

  const methodKeys = getMethodPermissionKeys(treeData.value)
  checkedKeys.value = [...new Set([...checkedKeys.value, ...methodKeys])]
}

// 监听选中权限变化
watch(
  () => props.selectedPermissions,
  (newPermissions) => {
    checkedKeys.value = [...newPermissions]
  },
  { immediate: true }
)

// 初始化展开状态
watch(
  treeData,
  () => {
    nextTick(() => {
      // 默认展开第一级（模块级别）
      expandedKeys.value = treeData.value.map((node) => node.key)
    })
  },
  { immediate: true }
)
</script>

<style scoped>
.permission-tree-v2 {
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.search-input {
  width: 250px;
}

.tree-container {
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  overflow: hidden;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.node-icon {
  flex-shrink: 0;
}

.node-label {
  font-weight: 500;
  flex-shrink: 0;
}

.method-tag {
  flex-shrink: 0;
}

.node-description {
  color: #999;
  font-size: 12px;
  margin-left: auto;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  max-width: 200px;
}

:deep(.n-tree-node-content) {
  padding: 4px 8px;
}

:deep(.tree-node-module .n-tree-node-content) {
  font-weight: 600;
  background-color: #f8f9fa;
}

:deep(.tree-node-resource .n-tree-node-content) {
  font-weight: 500;
  background-color: #f1f3f4;
}

:deep(.tree-node-method .n-tree-node-content) {
  background-color: #f9f9f9;
}

.permission-stats {
  font-size: 14px;
}

.batch-operations {
  border-top: 1px solid #e0e0e6;
  padding-top: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-2 {
  margin-top: 8px;
}
</style>
