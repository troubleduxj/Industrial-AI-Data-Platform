<template>
  <div class="menu-permission-tree">
    <!-- 搜索框 -->
    <div class="search-section">
      <n-input
        v-model:value="searchPattern"
        placeholder="搜索菜单..."
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
        <n-tag type="info" size="small"> 总计: {{ totalMenuCount }} 个菜单 </n-tag>
        <n-tag type="success" size="small"> 已选: {{ selectedMenus.length }} 个 </n-tag>
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

    <!-- 菜单权限树 -->
    <div class="tree-section">
      <n-tree
        ref="treeRef"
        :data="filteredMenuTree"
        :checked-keys="checkedKeys"
        :indeterminate-keys="indeterminateKeys"
        :expanded-keys="expandedKeys"
        :pattern="searchPattern"
        :show-irrelevant-nodes="false"
        key-field="id"
        label-field="title"
        children-field="children"
        checkable
        :cascade="true"
        :check-strategy="'all'"
        :block-line="true"
        :selectable="false"
        :render-label="renderMenuLabel"
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
 * 菜单权限树组件
 * 按照路由层级结构展示菜单权限，支持一级菜单 -> 二级菜单 -> 组件的层级结构
 */

// Props定义
const props = defineProps({
  // 菜单数据
  menuData: {
    type: Array,
    default: () => [],
  },
  // 已选中的菜单ID列表
  selectedMenus: {
    type: Array,
    default: () => [],
  },
  // 是否显示路由路径
  showRoutePath: {
    type: Boolean,
    default: true,
  },
  // 是否显示组件信息
  showComponent: {
    type: Boolean,
    default: true,
  },
})

// Emits定义
const emit = defineEmits(['update:selectedMenus', 'menuSelectionChange'])

// 响应式数据
const treeRef = ref(null)
const searchPattern = ref('')
const expandedKeys = ref([])
const checkedKeys = ref([])
const indeterminateKeys = ref([])

/**
 * 计算菜单总数
 */
const totalMenuCount = computed(() => {
  const countMenus = (menus) => {
    let count = 0
    menus.forEach((menu) => {
      count++
      if (menu.children && menu.children.length > 0) {
        count += countMenus(menu.children)
      }
    })
    return count
  }
  return countMenus(menuTree.value)
})

/**
 * 构建菜单树结构
 * 按照路由层级组织：一级菜单 -> 二级菜单 -> 组件
 */
const menuTree = computed(() => {
  if (!props.menuData || props.menuData.length === 0) {
    return []
  }

  // 如果数据已经是树结构，直接处理
  if (props.menuData.some((menu) => menu.children && menu.children.length > 0)) {
    return buildTreeFromHierarchy(props.menuData)
  }

  // 如果是平铺数据，需要构建树结构
  return buildTreeFromFlat(props.menuData)
})

/**
 * 从已有层级结构构建树
 */
const buildTreeFromHierarchy = (menus, parentPath = '') => {
  return menus
    // 不再过滤按钮类型，显示所有类型的菜单项
    .map((menu) => {
      // 按钮类型不需要路径拼接
      const currentPath = menu.type === 'button' 
        ? '' 
        : (parentPath ? `${parentPath}/${menu.path}` : menu.path)

      const treeNode = {
        id: menu.id,
        title: menu.title || menu.name,
        path: menu.path,
        fullPath: currentPath,
        type: menu.type,
        component: menu.component,
        icon: menu.icon,
        level: menu.level || 1,
        sort: menu.sort || menu.order || 0,
        visible: menu.visible !== false,
        perms: menu.perms || menu.permission, // 权限标识（按钮权限）
        children: [],
      }

      // 递归处理子菜单
      if (menu.children && menu.children.length > 0) {
        treeNode.children = buildTreeFromHierarchy(menu.children, currentPath)
      }

      return treeNode
    })
    .sort((a, b) => (a.sort || 0) - (b.sort || 0)) // 按排序字段排序
}

/**
 * 从平铺数据构建树结构
 */
const buildTreeFromFlat = (menus) => {
  // 不再过滤按钮类型，保留所有菜单项
  const filteredMenus = menus

  // 创建菜单映射
  const menuMap = new Map()
  const rootMenus = []

  // 第一遍：创建所有节点
  filteredMenus.forEach((menu) => {
    const treeNode = {
      id: menu.id,
      title: menu.title || menu.name,
      path: menu.path,
      fullPath: menu.path,
      type: menu.type,
      component: menu.component,
      icon: menu.icon,
      level: menu.level || 1,
      sort: menu.sort || menu.order || 0,
      visible: menu.visible !== false,
      parent_id: menu.parent_id,
      perms: menu.perms || menu.permission, // 权限标识
      children: [],
    }
    menuMap.set(menu.id, treeNode)
  })

  // 第二遍：建立父子关系
  menuMap.forEach((node) => {
    if (node.parent_id && node.parent_id !== 0) {
      const parent = menuMap.get(node.parent_id)
      if (parent) {
        parent.children.push(node)
        // 更新完整路径
        node.fullPath = parent.fullPath ? `${parent.fullPath}/${node.path}` : node.path
      } else {
        // 如果找不到父节点，作为根节点处理
        rootMenus.push(node)
      }
    } else {
      // 根节点
      rootMenus.push(node)
    }
  })

  // 递归排序所有层级
  const sortTree = (nodes) => {
    nodes.sort((a, b) => (a.sort || 0) - (b.sort || 0))
    nodes.forEach((node) => {
      if (node.children && node.children.length > 0) {
        sortTree(node.children)
      }
    })
    return nodes
  }

  return sortTree(rootMenus)
}

/**
 * 过滤后的菜单树（用于搜索）
 */
const filteredMenuTree = computed(() => {
  if (!searchPattern.value) {
    return menuTree.value
  }

  const filterTree = (nodes) => {
    return nodes.filter((node) => {
      const matchesSearch =
        node.title.toLowerCase().includes(searchPattern.value.toLowerCase()) ||
        (node.path && node.path.toLowerCase().includes(searchPattern.value.toLowerCase())) ||
        (node.component && node.component.toLowerCase().includes(searchPattern.value.toLowerCase()))

      if (node.children && node.children.length > 0) {
        const filteredChildren = filterTree(node.children)
        if (filteredChildren.length > 0) {
          return {
            ...node,
            children: filteredChildren,
          }
        }
      }

      return matchesSearch
    })
  }

  return filterTree(menuTree.value)
})

/**
 * 自定义菜单标签渲染（增强版 - 支持按钮权限）
 */
const renderMenuLabel = ({ option }) => {
  const elements = []

  // 根据类型添加不同的图标
  const iconMap = {
    catalog: '📁',
    menu: '📄',
    button: '🔘'
  }
  
  const iconColorMap = {
    catalog: '#1890ff',
    menu: '#52c41a',
    button: '#faad14'
  }

  if (option.type && iconMap[option.type]) {
    elements.push(
      h('span', {
        style: {
          marginRight: '6px',
          fontSize: '16px',
          color: iconColorMap[option.type] || '#666'
        }
      }, iconMap[option.type])
    )
  }

  // 菜单标题
  elements.push(
    h('span', { 
      class: 'menu-title',
      style: option.type === 'button' ? {
        fontSize: '13px',
        color: '#666'
      } : {}
    }, option.title)
  )

  // 按钮类型显示权限标识（HTTP方法）
  if (option.type === 'button' && option.perms) {
    const method = option.perms.split(' ')[0] // 提取HTTP方法
    const methodColors = {
      'GET': 'success',
      'POST': 'info',
      'PUT': 'warning',
      'DELETE': 'error',
      'PATCH': 'default'
    }
    
    elements.push(
      h(
        NTag,
        {
          size: 'tiny',
          type: methodColors[method] || 'default',
          bordered: false,
          style: { marginLeft: '8px' },
        },
        { default: () => method }
      )
    )
  }

  // 路由路径（只对非按钮类型显示）
  if (props.showRoutePath && option.path && option.type !== 'button') {
    elements.push(
      h(
        'span',
        {
          class: 'menu-path',
          style: { marginLeft: '8px', color: '#999', fontSize: '12px' },
        },
        `(${option.fullPath})`
      )
    )
  }

  // 组件信息（只对非按钮类型显示）
  if (props.showComponent && option.component && option.type !== 'button') {
    elements.push(
      h(
        NTooltip,
        {
          trigger: 'hover',
        },
        {
          trigger: () =>
            h(
              'span',
              {
                class: 'menu-component',
                style: { marginLeft: '8px', color: '#666', fontSize: '11px' },
              },
              '[组件]'
            ),
          default: () => option.component,
        }
      )
    )
  }

  // 菜单类型标签
  if (option.type) {
    const typeColors = {
      catalog: 'info',
      menu: 'success',
      button: 'warning',
    }
    
    const typeLabels = {
      catalog: '目录',
      menu: '菜单',
      button: '按钮',
    }

    elements.push(
      h(
        NTag,
        {
          size: 'tiny',
          type: typeColors[option.type] || 'default',
          style: { marginLeft: '8px' },
        },
        { default: () => typeLabels[option.type] || option.type }
      )
    )
  }

  return h('div', { class: 'menu-label-wrapper' }, elements)
}

/**
 * 处理选中状态变化
 */
const handleCheckedKeysChange = (keys, option) => {
  console.log('菜单权限树选中状态变化:', keys, option)
  checkedKeys.value = keys

  // 发送更新事件
  emit('update:selectedMenus', keys)
  emit('menuSelectionChange', {
    selectedMenus: keys,
    selectedCount: keys.length,
    totalCount: totalMenuCount.value,
  })
}

/**
 * 处理半选状态变化
 */
const handleIndeterminateKeysChange = (keys) => {
  console.log('菜单权限树半选状态变化:', keys)
  indeterminateKeys.value = keys
}

/**
 * 处理展开状态变化
 */
const handleExpandedKeysChange = (keys) => {
  expandedKeys.value = keys
}

/**
 * 全选菜单
 */
const selectAll = () => {
  const getAllMenuIds = (menus) => {
    const ids = []
    menus.forEach((menu) => {
      ids.push(menu.id)
      if (menu.children && menu.children.length > 0) {
        ids.push(...getAllMenuIds(menu.children))
      }
    })
    return ids
  }

  const allIds = getAllMenuIds(menuTree.value)
  checkedKeys.value = allIds
  indeterminateKeys.value = []
  handleCheckedKeysChange(allIds)
}

/**
 * 清空选择
 */
const clearAll = () => {
  checkedKeys.value = []
  indeterminateKeys.value = []
  handleCheckedKeysChange([])
}

/**
 * 展开全部
 */
const expandAll = () => {
  const getAllMenuIds = (menus) => {
    const ids = []
    menus.forEach((menu) => {
      ids.push(menu.id)
      if (menu.children && menu.children.length > 0) {
        ids.push(...getAllMenuIds(menu.children))
      }
    })
    return ids
  }

  expandedKeys.value = getAllMenuIds(menuTree.value)
}

/**
 * 收起全部
 */
const collapseAll = () => {
  expandedKeys.value = []
}

/**
 * 初始化展开状态
 */
const initializeExpandedKeys = () => {
  // 默认收起所有菜单
  expandedKeys.value = []
}

// 监听菜单数据变化
watch(
  () => props.menuData,
  () => {
    initializeExpandedKeys()
  },
  { immediate: true }
)

// 监听selectedMenus属性变化
watch(
  () => props.selectedMenus,
  (newSelectedMenus) => {
    console.log('MenuPermissionTree 接收到新的selectedMenus:', newSelectedMenus)
    if (Array.isArray(newSelectedMenus)) {
      checkedKeys.value = [...newSelectedMenus]
      // 当外部传入新的选中状态时，清空半选状态，让树组件重新计算
      indeterminateKeys.value = []
    }
  },
  { immediate: true, deep: true }
)

// 组件挂载时初始化
onMounted(() => {
  initializeExpandedKeys()
})
</script>

<style scoped>
.menu-permission-tree {
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

.menu-label-wrapper {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.menu-title {
  font-weight: 500;
}

.menu-path {
  font-family: 'Courier New', monospace;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
}

.menu-component {
  font-style: italic;
}

/* 树节点样式优化 */
:deep(.n-tree-node-content) {
  padding: 4px 0;
}

:deep(.n-tree-node-content:hover) {
  background-color: #f5f7fa;
}

:deep(.n-tree-node-wrapper) {
  padding: 2px 0;
}

/* 不同层级的缩进样式 */
:deep(.n-tree-node[data-level='1']) {
  font-weight: 600;
}

:deep(.n-tree-node[data-level='2']) {
  font-weight: 500;
}

:deep(.n-tree-node[data-level='3']) {
  font-weight: 400;
  font-size: 13px;
}

/* 按钮权限节点的特殊样式 */
:deep(.n-tree-node-content__text:has(.menu-label-wrapper:has([style*="button"]))) {
  background-color: #fffbf0;
  border-left: 3px solid #faad14;
  padding-left: 8px;
}

/* 按钮节点悬停效果 */
:deep(.n-tree-node-content:hover:has(.menu-label-wrapper:has([style*="button"]))) {
  background-color: #fff7e6;
}
</style>
