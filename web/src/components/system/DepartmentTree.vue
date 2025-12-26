<template>
  <div class="department-tree">
    <n-tree
      :data="treeData"
      :checkable="checkable"
      :checked-keys="checkedKeys"
      :expanded-keys="expandedKeys"
      :selectable="selectable"
      :selected-keys="selectedKeys"
      block-line
      @update:checked-keys="handleCheckedKeysChange"
      @update:selected-keys="handleSelectedKeysChange"
      @update:expanded-keys="handleExpandedKeysChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  checkable: {
    type: Boolean,
    default: false,
  },
  selectable: {
    type: Boolean,
    default: true,
  },
  checkedKeys: {
    type: Array,
    default: () => [],
  },
  selectedKeys: {
    type: Array,
    default: () => [],
  },
  expandedKeys: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:checkedKeys', 'update:selectedKeys', 'update:expandedKeys'])

const treeData = computed(() => {
  return formatTreeData(props.data)
})

function formatTreeData(data) {
  return data.map((item) => ({
    key: item.id,
    label: item.name,
    children: item.children ? formatTreeData(item.children) : undefined,
  }))
}

function handleCheckedKeysChange(keys) {
  emit('update:checkedKeys', keys)
}

function handleSelectedKeysChange(keys) {
  emit('update:selectedKeys', keys)
}

function handleExpandedKeysChange(keys) {
  emit('update:expandedKeys', keys)
}
</script>

<style scoped>
.department-tree {
  width: 100%;
}
</style>
