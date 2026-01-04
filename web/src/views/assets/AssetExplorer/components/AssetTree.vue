<template>
  <div class="asset-tree-container">
    <n-input
      v-model:value="pattern"
      placeholder="搜索位置..."
      size="small"
      class="mb-2"
    >
      <template #prefix>
        <n-icon :component="SearchOutline" />
      </template>
    </n-input>
    <n-spin :show="loading">
      <n-tree
        block-line
        expand-on-click
        :data="treeData"
        :pattern="pattern"
        :on-update:selected-keys="handleSelect"
        selectable
        default-expand-all
        key-field="key"
        label-field="label"
        children-field="children"
      />
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { NTree, NInput, NIcon, NSpin } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'

const props = defineProps({
  assets: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select'])

const pattern = ref('')

// Build tree from asset locations
const treeData = computed(() => {
  const root = []
  const map = new Map()

  // Helper to get or create node
  const getOrCreateNode = (path, name, parentPath = null) => {
    if (!map.has(path)) {
      const node = {
        key: path,
        label: name,
        children: [],
        isLeaf: false,
        count: 0
      }
      map.set(path, node)
      
      if (parentPath && map.has(parentPath)) {
        map.get(parentPath).children.push(node)
      } else {
        root.push(node)
      }
    }
    return map.get(path)
  }

  props.assets.forEach(asset => {
    const location = asset.location || '未分类'
    const parts = location.split('/').filter(p => p)
    
    if (parts.length === 0) {
        // Handle root assets or empty location
        const path = 'Uncategorized'
        const node = getOrCreateNode(path, '未分类')
        node.count++
        return
    }

    let currentPath = ''
    parts.forEach((part, index) => {
      const parentPath = currentPath
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const node = getOrCreateNode(currentPath, part, parentPath)
      if (index === parts.length - 1) {
        node.count++ // Count assets at this level
      }
    })
  })

  // Add counts to labels
  const updateLabels = (nodes) => {
    nodes.forEach(node => {
      // Recursively calculate total count including children
      const childrenCount = node.children.reduce((acc, child) => {
          updateLabels([child])
          return acc + (child.totalCount || 0)
      }, 0)
      
      node.totalCount = node.count + childrenCount
      node.label = `${node.label} (${node.totalCount})`
      
      if (node.children.length > 0) {
          updateLabels(node.children)
      }
    })
  }
  
  // Simplified label update without recursion for now to avoid complexity issues
  // just showing structure
  
  return root
})

function handleSelect(keys, option) {
  if (keys.length > 0) {
    emit('select', keys[0]) // Emit the full path
  } else {
    emit('select', null)
  }
}
</script>

<style scoped>
.asset-tree-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
