<!--
权限树形选择组件
用于角色权限管理的树形权限选择器
-->
<template>
  <div class="permission-tree">
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
        :cascade="false"
        checkable
        block-line
        virtual-scroll
        :height="400"
        :node-props="nodeProps"
        @update:checked-keys="handleCheckedKeysChange"
        @update:expanded-keys="handleExpandedKeysChange"
      >
        <template #default="{ option }">
          <div class="tree-node">
            <n-icon class="node-icon" :color="getNodeIconColor(option)">
              <component :is="getNodeIcon(option)" />
            </n-icon>
            <span class="node-label">{{ option.label }}</span>
            <n-tag
              v-if="option.method"
              :type="getMethodTagType(option.method)"
              size="small"
              class="method-tag"
            >
              {{ option.method }}
            </n-tag>
            <span v-if="option.description" class="node-description">
              {{ option.description }}
            </span>
          </div>
        </template>
      </n-tree>
    </div>

    <!-- 批量操作 -->
    <div class="batch-operations mt-4">
      <n-collapse>
        <n-collapse-item title="批量操作" name="batch">
          <n-space vertical>
            <div>
              <n-text strong>按模块批量选择：</n-text>
              <n-space class="mt-2">
                <n-button
                  v-for="module in modules"
                  :key="module.key"
                  size="small"
                  @click="selectModule(module.key)"
                >
                  {{ module.label }}
                </n-button>
              </n-space>
            </div>

            <div>
              <n-text strong>按操作类型批量选择：</n-text>
              <n-space class="mt-2">
                <n-button
                  v-for="action in actions"
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
import { ref, computed, watch, nextTick } from 'vue'
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
} from '@vicons/ionicons5'
import { safeDOMOperation, isElementSafe } from '@/utils/dom-safety'

const props = defineProps({
  // 权限数据
  permissions: {
    type: Array,
    default: () => [],
  },
  // 已选中的权限
  selectedPermissions: {
    type: Array,
    default: () => [],
  },
  // 是否只读
  readonly: {
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

// 模块配置
const modules = [
  { key: 'user', label: '用户管理' },
  { key: 'role', label: '角色管理' },
  { key: 'menu', label: '菜单管理' },
  { key: 'api', label: 'API管理' },
  { key: 'system', label: '系统管理' },
  { key: 'device', label: '设备管理' },
  { key: 'alarm', label: '报警管理' },
]

// 操作类型配置
const actions = [
  { method: 'GET', label: '查询' },
  { method: 'POST', label: '新增' },
  { method: 'PUT', label: '修改' },
  { method: 'DELETE', label: '删除' },
]

// 构建树形数据
const treeData = computed(() => {
  const tree = {}

  props.permissions.forEach((permission) => {
    const { path, method, summary, tags } = permission
    const pathParts = path.split('/').filter((part) => part)

    // 确定模块名称
    let moduleName = tags || '其他'
    if (pathParts.length > 2) {
      const resourceName = pathParts[2]
      const moduleConfig = modules.find((m) => resourceName.includes(m.key) || path.includes(m.key))
      if (moduleConfig) {
        moduleName = moduleConfig.label
      }
    }

    // 构建树结构
    if (!tree[moduleName]) {
      tree[moduleName] = {
        key: `module_${moduleName}`,
        label: moduleName,
        type: 'module',
        children: {},
      }
    }

    // 按HTTP方法分组
    const methodGroup = `${method}操作`
    if (!tree[moduleName].children[methodGroup]) {
      tree[moduleName].children[methodGroup] = {
        key: `${moduleName}_${method}`,
        label: methodGroup,
        type: 'method',
        method: method,
        children: [],
      }
    }

    // 添加具体的API
    tree[moduleName].children[methodGroup].children.push({
      key: `${method}_${path}`,
      label: summary || path,
      type: 'api',
      method: method,
      path: path,
      description: path,
      permission: permission,
    })
  })

  // 转换为数组格式
  return Object.values(tree).map((module) => ({
    ...module,
    children: Object.values(module.children).map((methodGroup) => ({
      ...methodGroup,
      children: methodGroup.children,
    })),
  }))
})

// 过滤后的树形数据
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
          (node.path && node.path.toLowerCase().includes(keyword))

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
  const countNodes = (nodes) => {
    return nodes.reduce((count, node) => {
      if (node.type === 'api') {
        return count + 1
      }
      if (node.children) {
        return count + countNodes(node.children)
      }
      return count
    }, 0)
  }
  return countNodes(treeData.value)
})

const filteredCount = computed(() => {
  const countNodes = (nodes) => {
    return nodes.reduce((count, node) => {
      if (node.type === 'api') {
        return count + 1
      }
      if (node.children) {
        return count + countNodes(node.children)
      }
      return count
    }, 0)
  }
  return countNodes(filteredTreeData.value)
})

const selectedCount = computed(() => {
  return checkedKeys.value.filter((key) => key.includes('_/api/')).length
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

// 获取节点图标
const getNodeIcon = (option) => {
  switch (option.type) {
    case 'module':
      if (option.label.includes('用户')) return UserIcon
      if (option.label.includes('系统')) return SystemIcon
      if (option.label.includes('安全')) return SecurityIcon
      return FolderIcon
    case 'method':
      return FolderIcon
    case 'api':
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
    case 'method':
      return '#18a058'
    case 'api':
      return '#f0a020'
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

// 事件处理
const handleCheckedKeysChange = (keys) => {
  try {
    if (!Array.isArray(keys)) {
      console.warn('权限树选中状态变化：keys不是数组', keys)
      return
    }

    checkedKeys.value = keys

    // 提取API权限
    const apiKeys = keys.filter((key) => key && typeof key === 'string' && key.includes('_/api/'))
    const selectedPermissions = apiKeys
      .map((key) => {
        const [method, path] = key.split('_', 2)
        return props.permissions.find((p) => p.method === method && p.path === path)
      })
      .filter(Boolean)

    emit('update:selectedPermissions', selectedPermissions)
    emit('change', selectedPermissions)
  } catch (error) {
    console.error('权限树选中状态变化处理失败:', error)
  }
}

const handleExpandedKeysChange = (keys) => {
  expandedKeys.value = keys
}

// 工具方法
const expandAll = () => {
  try {
    const getAllKeys = (nodes) => {
      if (!Array.isArray(nodes)) return []
      const keys = []
      nodes.forEach((node) => {
        if (node && node.key) {
          keys.push(node.key)
          if (node.children && Array.isArray(node.children)) {
            keys.push(...getAllKeys(node.children))
          }
        }
      })
      return keys
    }

    if (treeData.value && Array.isArray(treeData.value)) {
      expandedKeys.value = getAllKeys(treeData.value)
    }
  } catch (error) {
    console.error('展开所有节点失败:', error)
  }
}

const collapseAll = () => {
  expandedKeys.value = []
}

const selectAll = () => {
  try {
    const getAllApiKeys = (nodes) => {
      if (!Array.isArray(nodes)) return []
      const keys = []
      nodes.forEach((node) => {
        if (node && node.key) {
          if (node.type === 'api') {
            keys.push(node.key)
          }
          if (node.children && Array.isArray(node.children)) {
            keys.push(...getAllApiKeys(node.children))
          }
        }
      })
      return keys
    }

    if (treeData.value && Array.isArray(treeData.value)) {
      checkedKeys.value = getAllApiKeys(treeData.value)
    }
  } catch (error) {
    console.error('全选失败:', error)
  }
}

const clearAll = () => {
  checkedKeys.value = []
}

const selectModule = (moduleKey) => {
  const moduleConfig = modules.find((m) => m.key === moduleKey)
  if (!moduleConfig) return

  const getModuleApiKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.label === moduleConfig.label) {
        const getApiKeys = (children) => {
          children.forEach((child) => {
            if (child.type === 'api') {
              keys.push(child.key)
            }
            if (child.children) {
              getApiKeys(child.children)
            }
          })
        }
        if (node.children) {
          getApiKeys(node.children)
        }
      }
    })
    return keys
  }

  const moduleKeys = getModuleApiKeys(treeData.value)
  checkedKeys.value = [...new Set([...checkedKeys.value, ...moduleKeys])]
}

const selectByMethod = (method) => {
  const getMethodApiKeys = (nodes) => {
    const keys = []
    nodes.forEach((node) => {
      if (node.type === 'api' && node.method === method) {
        keys.push(node.key)
      }
      if (node.children) {
        keys.push(...getMethodApiKeys(node.children))
      }
    })
    return keys
  }

  const methodKeys = getMethodApiKeys(treeData.value)
  checkedKeys.value = [...new Set([...checkedKeys.value, ...methodKeys])]
}

// 监听选中权限变化
watch(
  () => props.selectedPermissions,
  async (newPermissions) => {
    await safeDOMOperation(
      () => {
        console.log('PermissionTree watch触发，接收到权限:', newPermissions)
        if (newPermissions && Array.isArray(newPermissions) && newPermissions.length > 0) {
          const keys = newPermissions.map((p) => {
            const key = `${p.method}_${p.path}`
            console.log('生成key:', key, '来源:', p)
            return key
          })
          console.log('设置checkedKeys:', keys)
          checkedKeys.value = keys
        } else {
          console.log('清空checkedKeys')
          checkedKeys.value = []
        }
      },
      { errorMessage: '更新选中权限失败' }
    )
  },
  { immediate: true, deep: true }
)

// 初始化展开状态
watch(
  treeData,
  async () => {
    await nextTick()
    await safeDOMOperation(
      () => {
        // 检查treeRef是否存在且已挂载
        if (treeRef.value && treeData.value && Array.isArray(treeData.value)) {
          // 默认展开第一级
          expandedKeys.value = treeData.value.map((node) => node.key)
        }
      },
      { errorMessage: '权限树展开状态初始化失败' }
    )
  },
  { immediate: true }
)
</script>

<style scoped>
.permission-tree {
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
}

:deep(.n-tree-node-content) {
  padding: 4px 8px;
}

:deep(.tree-node-module .n-tree-node-content) {
  font-weight: 600;
  background-color: #f8f9fa;
}

:deep(.tree-node-method .n-tree-node-content) {
  font-weight: 500;
  background-color: #f1f3f4;
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
