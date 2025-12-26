<template>
  <div class="api-permission-tree">
    <!-- 搜索框 -->
    <div class="search-section">
      <n-input
        v-model:value="searchPattern"
        placeholder="搜索接口..."
        clearable
        class="search-input"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <n-space>
        <n-tag type="info" size="small"> 总计: {{ totalApiCount }} 个接口 </n-tag>
        <n-tag type="success" size="small"> 已选: {{ selectedApis.length }} 个 </n-tag>
      </n-space>
    </div>

    <!-- 批量操作 -->
    <div class="batch-actions">
      <n-space>
        <n-button size="small" @click="selectAll"> 全选 </n-button>
        <n-button size="small" @click="clearAll"> 清空 </n-button>
        <n-button size="small" @click="expandAll"> 展开全部 </n-button>
        <n-button size="small" @click="collapseAll"> 收起全部 </n-button>
      </n-space>
    </div>

    <!-- 接口权限树 -->
    <div class="tree-section">
      <n-tree
        ref="treeRef"
        :data="filteredApiTree"
        :checked-keys="checkedKeys"
        :indeterminate-keys="indeterminateKeys"
        :expanded-keys="expandedKeys"
        :pattern="searchPattern"
        :show-irrelevant-nodes="false"
        key-field="unique_id"
        label-field="summary"
        children-field="children"
        checkable
        cascade
        :check-strategy="'all'"
        :block-line="true"
        :selectable="false"
        :render-label="renderApiLabel"
        :virtual-scroll="true"
        @update:checked-keys="handleCheckedKeysChange"
        @update:indeterminate-keys="handleIndeterminateKeysChange"
        @update:expanded-keys="handleExpandedKeysChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, h } from 'vue'
import { NTree, NInput, NIcon, NSpace, NTag, NButton, NTooltip } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'

/**
 * 接口权限树组件
 * 按照接口路径层级结构展示接口权限，支持路径分组的层级结构
 */

// Props定义
const props = defineProps({
  // 接口数据
  apiData: {
    type: Array,
    default: () => [],
  },
  // 已选中的接口ID列表
  selectedApis: {
    type: Array,
    default: () => [],
  },
  // 是否显示请求方法
  showMethod: {
    type: Boolean,
    default: true,
  },
  // 是否显示接口路径
  showPath: {
    type: Boolean,
    default: true,
  },
})

// Emits定义
const emit = defineEmits(['update:selectedApis', 'apiSelectionChange'])

// 响应式数据
const treeRef = ref(null)
const searchPattern = ref('')
const expandedKeys = ref([])
const checkedKeys = ref([])
const indeterminateKeys = ref([])

/**
 * 计算属性：过滤后的接口树数据
 */
const filteredApiTree = computed(() => {
  if (!searchPattern.value) {
    return props.apiData
  }
  return filterTreeData(props.apiData, searchPattern.value)
})

/**
 * 计算属性：总接口数量
 */
const totalApiCount = computed(() => {
  return countTreeNodes(props.apiData)
})

/**
 * 递归过滤树数据
 * @param {Array} data - 树数据
 * @param {string} pattern - 搜索模式
 * @returns {Array} 过滤后的数据
 */
function filterTreeData(data, pattern) {
  if (!data || !Array.isArray(data)) return []

  return data.reduce((filtered, node) => {
    const matchesPattern =
      node.summary?.toLowerCase().includes(pattern.toLowerCase()) ||
      node.path?.toLowerCase().includes(pattern.toLowerCase()) ||
      node.method?.toLowerCase().includes(pattern.toLowerCase())

    const filteredChildren = node.children ? filterTreeData(node.children, pattern) : []

    if (matchesPattern || filteredChildren.length > 0) {
      filtered.push({
        ...node,
        children: filteredChildren,
      })
    }

    return filtered
  }, [])
}

/**
 * 递归统计树节点数量
 * @param {Array} data - 树数据
 * @returns {number} 节点总数
 */
function countTreeNodes(data) {
  if (!data || !Array.isArray(data)) return 0

  return data.reduce((count, node) => {
    let nodeCount = 1 // 当前节点
    if (node.children && Array.isArray(node.children)) {
      nodeCount += countTreeNodes(node.children)
    }
    return count + nodeCount
  }, 0)
}

/**
 * 自定义渲染接口标签
 * @param {Object} info - 节点信息
 * @returns {VNode} 渲染的节点
 */
function renderApiLabel(info) {
  const { option } = info

  // 如果是分组节点（有children但没有unique_id）
  if (option.children && !option.unique_id) {
    return h(
      'span',
      {
        style: {
          fontWeight: 'bold',
          color: '#1890ff',
        },
      },
      option.summary || option.label
    )
  }

  // 接口节点
  const elements = []

  // 请求方法标签
  if (props.showMethod && option.method) {
    const methodColors = {
      GET: '#52c41a',
      POST: '#1890ff',
      PUT: '#fa8c16',
      PATCH: '#722ed1',
      DELETE: '#f5222d',
    }

    elements.push(
      h(
        'span',
        {
          style: {
            display: 'inline-block',
            padding: '4px 10px',
            marginRight: '12px',
            backgroundColor: methodColors[option.method] || '#666',
            color: 'white',
            fontSize: '11px',
            borderRadius: '3px',
            fontWeight: 'bold',
            minWidth: '60px',
            textAlign: 'center',
          },
        },
        option.method
      )
    )
  }

  // 接口名称 - 提取中文部分显示，完整内容作为tooltip
  const fullText = option.summary || option.label
  // 提取括号前的中文部分
  const displayText = fullText.split('(')[0].trim()
  // 提取括号内的内容作为tooltip
  const tooltipText = fullText.match(/\(([^)]+)\)/)?.[1] || fullText

  elements.push(
    h(
      'span',
      {
        style: {
          flex: '1',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          cursor: 'help',
        },
        title: tooltipText, // 鼠标悬浮时显示完整路径
      },
      displayText
    )
  )

  // 接口路径 - 已隐藏，只显示请求方法和接口名称
  // if (props.showPath && option.path) {
  //   elements.push(
  //     h(
  //       'span',
  //       {
  //         style: {
  //           color: '#666',
  //           fontSize: '12px',
  //           fontStyle: 'italic',
  //         },
  //       },
  //       `(${option.path})`
  //     )
  //   )
  // }

  return h(
    'div',
    {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
      },
    },
    elements
  )
}

/**
 * 处理选中状态变化
 * @param {Array} keys - 选中的键值列表
 */
function handleCheckedKeysChange(keys, option) {
  console.log('API权限树选中状态变化:', keys, option)
  checkedKeys.value = keys
  emit('update:selectedApis', keys)
  emit('apiSelectionChange', keys)
}

/**
 * 处理半选状态变化
 * @param {Array} keys - 半选的键值列表
 */
function handleIndeterminateKeysChange(keys) {
  console.log('API权限树半选状态变化:', keys)
  indeterminateKeys.value = keys
}

/**
 * 处理展开状态变化
 * @param {Array} expandedKeysParam - 展开的键值列表
 */
function handleExpandedKeysChange(expandedKeysParam) {
  expandedKeys.value = expandedKeysParam
}

/**
 * 全选操作
 */
function selectAll() {
  const allKeys = getAllNodeKeys(props.apiData)
  checkedKeys.value = allKeys
  indeterminateKeys.value = []
  emit('update:selectedApis', allKeys)
  emit('apiSelectionChange', allKeys)
}

/**
 * 清空选择
 */
function clearAll() {
  checkedKeys.value = []
  indeterminateKeys.value = []
  emit('update:selectedApis', [])
  emit('apiSelectionChange', [])
}

/**
 * 展开全部节点
 */
function expandAll() {
  const allKeys = getAllNodeKeys(filteredApiTree.value)
  expandedKeys.value = allKeys

  // 检查树组件是否已挂载且有setExpandedKeys方法
  if (treeRef.value && typeof treeRef.value.setExpandedKeys === 'function') {
    try {
      treeRef.value.setExpandedKeys(allKeys)
    } catch (error) {
      console.warn('ApiPermissionTree: setExpandedKeys failed:', error)
    }
  }
}

/**
 * 收起全部节点
 */
function collapseAll() {
  expandedKeys.value = []

  // 检查树组件是否已挂载且有setExpandedKeys方法
  if (treeRef.value && typeof treeRef.value.setExpandedKeys === 'function') {
    try {
      treeRef.value.setExpandedKeys([])
    } catch (error) {
      console.warn('ApiPermissionTree: setExpandedKeys failed:', error)
    }
  }
}

/**
 * 递归获取所有节点的键值
 * @param {Array} data - 树数据
 * @returns {Array} 所有节点的键值列表
 */
function getAllNodeKeys(data) {
  if (!data || !Array.isArray(data)) return []

  const keys = []

  function traverse(nodes) {
    nodes.forEach((node) => {
      if (node.unique_id) {
        keys.push(node.unique_id)
      }
      if (node.children && Array.isArray(node.children)) {
        traverse(node.children)
      }
    })
  }

  traverse(data)
  return keys
}

/**
 * 初始化展开的键值
 */
function initializeExpandedKeys() {
  // 默认收起所有接口
  expandedKeys.value = []

  // 检查树组件是否已挂载且有setExpandedKeys方法
  if (treeRef.value && typeof treeRef.value.setExpandedKeys === 'function') {
    try {
      treeRef.value.setExpandedKeys([])
    } catch (error) {
      console.warn('ApiPermissionTree: setExpandedKeys failed:', error)
    }
  }
}

// 监听接口数据变化，重新初始化展开状态
watch(
  () => props.apiData,
  () => {
    initializeExpandedKeys()
  },
  { immediate: true, deep: true }
)

// 监听选中接口的变化
watch(
  () => props.selectedApis,
  (newSelectedApis) => {
    console.log('ApiPermissionTree 接收到新的selectedApis:', newSelectedApis)
    if (Array.isArray(newSelectedApis)) {
      checkedKeys.value = [...newSelectedApis]
      // 当外部传入新的选中状态时，清空半选状态，让树组件重新计算
      indeterminateKeys.value = []
    }
  },
  { immediate: true, deep: true }
)

/**
 * 获取选中的数据
 * @returns {Array} 选中的API数据
 */
function getCheckedData() {
  if (!treeRef.value) {
    console.warn('ApiPermissionTree: treeRef is not available')
    return []
  }

  try {
    // 使用Naive UI Tree组件的getCheckedData方法
    const checkedResult = treeRef.value.getCheckedData()
    console.log('ApiPermissionTree getCheckedData - checkedResult:', checkedResult)

    // checkedResult格式: { keys: Array<string | number>, options: Array<TreeOption | null> }
    const checkedKeys = checkedResult?.keys || []
    console.log('ApiPermissionTree getCheckedData - checkedKeys:', checkedKeys)

    // 从apiData中找到对应的完整数据
    const checkedData = []

    function findCheckedNodes(nodes) {
      if (!nodes || !Array.isArray(nodes)) return

      nodes.forEach((node) => {
        if (node.unique_id && checkedKeys.includes(node.unique_id)) {
          checkedData.push({
            id: node.id,
            unique_id: node.unique_id,
            path: node.path,
            method: node.method,
            summary: node.summary,
          })
        }

        if (node.children && Array.isArray(node.children)) {
          findCheckedNodes(node.children)
        }
      })
    }

    findCheckedNodes(props.apiData)
    console.log('ApiPermissionTree getCheckedData - result:', checkedData)
    return checkedData
  } catch (error) {
    console.error('ApiPermissionTree getCheckedData error:', error)
    return []
  }
}

// 暴露方法给父组件
defineExpose({
  getCheckedData,
  selectAll,
  clearAll,
  expandAll,
  collapseAll,
})

// 组件挂载后初始化
onMounted(() => {
  initializeExpandedKeys()
})
</script>

<style scoped>
.api-permission-tree {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.search-section {
  flex-shrink: 0;
}

.search-input {
  width: 100%;
}

.stats-section {
  flex-shrink: 0;
  padding: 8px 0;
}

.batch-actions {
  flex-shrink: 0;
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.tree-section {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 300px;
  max-height: calc(100vh - 400px); /* 根据抽屉高度动态调整 */
  
  /* 自定义滚动条样式 - 默认隐藏 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.tree-section::-webkit-scrollbar {
  width: 0; /* Chrome, Safari, Opera - 默认隐藏 */
  height: 0;
}

/* 鼠标悬浮时显示滚动条 */
.tree-section:hover {
  scrollbar-width: thin; /* Firefox */
  -ms-overflow-style: auto; /* IE and Edge */
}

.tree-section:hover::-webkit-scrollbar {
  width: 6px; /* Chrome, Safari, Opera - 悬浮时显示 */
}

.tree-section:hover::-webkit-scrollbar-track {
  background: transparent;
}

.tree-section:hover::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
  transition: background-color 0.2s;
}

.tree-section:hover::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

/* 树组件样式优化 */
:deep(.n-tree .n-tree-node) {
  margin: 2px 0;
}

:deep(.n-tree .n-tree-node-content) {
  padding: 4px 8px;
  border-radius: 4px;
}

:deep(.n-tree .n-tree-node-content:hover) {
  background-color: var(--hover-color);
}

:deep(.n-tree .n-checkbox) {
  margin-right: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .batch-actions {
    overflow-x: auto;
  }

  .batch-actions .n-space {
    flex-wrap: nowrap;
  }
}
</style>
