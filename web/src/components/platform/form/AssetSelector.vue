<template>
  <NSelect
    :value="modelValue"
    :options="assetOptions"
    :loading="loading"
    :placeholder="placeholder"
    clearable
    filterable
    remote
    :disabled="disabled"
    :clear-filter-after-select="false"
    @search="handleSearch"
    @update:value="handleSelect"
  >
    <template #empty>
      <div class="py-4 text-center">
        <div v-if="loading">正在搜索资产...</div>
        <div v-else-if="searchKeyword">未找到相关资产</div>
        <div v-else>请输入资产编号或名称进行搜索</div>
      </div>
    </template>

    <template #option="{ node, option }">
      <div class="asset-option">
        <div class="asset-info">
          <div class="asset-code">{{ option.code }}</div>
          <div class="asset-name">{{ option.name }}</div>
        </div>
        <div class="asset-meta">
          <NTag size="small" type="info">{{ option.category_name }}</NTag>
          <StatusIndicator :status="option.status" type="device" size="small" />
        </div>
      </div>
    </template>
  </NSelect>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { NSelect, NTag } from 'naive-ui'
import StatusIndicator from '@/components/common/StatusIndicator.vue'
import { assetApi } from '@/api/v4'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: null,
  },
  categoryId: {
    type: [String, Number],
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  placeholder: {
    type: String,
    default: '请选择资产',
  },
  // 是否显示状态
  showStatus: {
    type: Boolean,
    default: true,
  },
  // 是否自动加载
  autoLoad: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const assets = ref([])
const searchKeyword = ref('')

// Load assets
async function loadAssets() {
  loading.value = true
  try {
    const params = {
      keyword: searchKeyword.value,
      category_id: props.categoryId
    }
    const res = await assetApi.getList(params)
    assets.value = res.data?.items || res.data || []
  } catch (err) {
    console.error('Failed to load assets:', err)
  } finally {
    loading.value = false
  }
}

// Options
const assetOptions = computed(() => {
  return assets.value.map(asset => ({
    label: `${asset.code} - ${asset.name}`,
    value: asset.id,
    code: asset.code,
    name: asset.name,
    category_id: asset.category_id || asset.category?.id,
    category_code: asset.category_code || asset.category?.code,
    category_name: asset.category?.name || asset.category_name || '',
    status: asset.status
  }))
})

// Handlers
function handleSearch(val) {
  searchKeyword.value = val
  loadAssets()
}

function handleSelect(val, option) {
  emit('update:modelValue', val)
  emit('change', option)
}

watch(() => props.categoryId, () => {
    loadAssets()
})

onMounted(() => {
  if (props.autoLoad) {
      loadAssets()
  }
})
</script>

<style scoped>
.asset-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}
.asset-info {
  flex: 1;
}
.asset-code {
  font-weight: 600;
  color: var(--n-text-color-1);
  font-size: 14px;
}
.asset-name {
  color: var(--n-text-color-2);
  font-size: 12px;
  margin-top: 2px;
}
.asset-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
