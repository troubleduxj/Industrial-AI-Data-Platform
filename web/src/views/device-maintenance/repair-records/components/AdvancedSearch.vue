<template>
  <div class="advanced-search">
    <NCard>
      <div class="search-container">
        <!-- 基础搜索行 -->
        <div class="search-row">
          <QueryBarItem label="焊机编号">
            <NInput
              v-model:value="searchForm.device_number"
              placeholder="请输入焊机编号"
              clearable
              style="width: 200px"
            />
          </QueryBarItem>

          <QueryBarItem label="申请人">
            <NInput
              v-model:value="searchForm.applicant"
              placeholder="请输入申请人"
              clearable
              style="width: 200px"
            />
          </QueryBarItem>

          <QueryBarItem label="品牌">
            <NSelect
              v-model:value="searchForm.brand"
              :options="brandOptions"
              placeholder="请选择品牌"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>

          <QueryBarItem label="故障状态">
            <NSelect
              v-model:value="searchForm.is_fault"
              :options="faultStatusOptions"
              placeholder="请选择状态"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>
        </div>

        <!-- 高级搜索行 -->
        <div v-show="showAdvanced" class="search-row advanced-row">
          <QueryBarItem label="报修日期">
            <NDatePicker
              v-model:value="searchForm.repair_date_range"
              type="daterange"
              placeholder="请选择日期范围"
              style="width: 300px"
            />
          </QueryBarItem>

          <QueryBarItem label="公司">
            <NInput
              v-model:value="searchForm.company"
              placeholder="请输入公司名称"
              clearable
              style="width: 200px"
            />
          </QueryBarItem>

          <QueryBarItem label="部门">
            <NInput
              v-model:value="searchForm.department"
              placeholder="请输入部门"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>

          <QueryBarItem label="车间">
            <NInput
              v-model:value="searchForm.workshop"
              placeholder="请输入车间"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>
        </div>

        <!-- 更多高级搜索选项 -->
        <div v-show="showAdvanced" class="search-row advanced-row">
          <QueryBarItem label="设备类别">
            <NSelect
              v-model:value="searchForm.category"
              :options="categoryOptions"
              placeholder="请选择设备类别"
              clearable
              style="width: 180px"
            />
          </QueryBarItem>

          <QueryBarItem label="故障原因">
            <NSelect
              v-model:value="searchForm.fault_reason"
              :options="faultReasonOptions"
              placeholder="请选择故障原因"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>

          <QueryBarItem label="损坏类别">
            <NSelect
              v-model:value="searchForm.damage_category"
              :options="damageCategoryOptions"
              placeholder="请选择损坏类别"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>

          <QueryBarItem label="维修人">
            <NInput
              v-model:value="searchForm.repairer"
              placeholder="请输入维修人"
              clearable
              style="width: 150px"
            />
          </QueryBarItem>
        </div>

        <!-- 快捷筛选 -->
        <div v-show="showAdvanced" class="quick-filters">
          <div class="filter-group">
            <span class="filter-label">快捷筛选：</span>
            <NButton
              size="small"
              :type="quickFilter === 'today' ? 'primary' : 'default'"
              @click="setQuickFilter('today')"
            >
              今日报修
            </NButton>
            <NButton
              size="small"
              :type="quickFilter === 'week' ? 'primary' : 'default'"
              @click="setQuickFilter('week')"
            >
              本周报修
            </NButton>
            <NButton
              size="small"
              :type="quickFilter === 'month' ? 'primary' : 'default'"
              @click="setQuickFilter('month')"
            >
              本月报修
            </NButton>
            <NButton
              size="small"
              :type="quickFilter === 'fault' ? 'primary' : 'default'"
              @click="setQuickFilter('fault')"
            >
              故障记录
            </NButton>
            <NButton
              size="small"
              :type="quickFilter === 'maintenance' ? 'primary' : 'default'"
              @click="setQuickFilter('maintenance')"
            >
              维护记录
            </NButton>
          </div>
        </div>

        <!-- 搜索历史 -->
        <div v-show="showAdvanced && searchHistory.length > 0" class="search-history">
          <div class="history-group">
            <span class="history-label">搜索历史：</span>
            <NTag
              v-for="(history, index) in searchHistory"
              :key="index"
              closable
              size="small"
              style="margin-right: 8px; margin-bottom: 4px"
              @click="applySearchHistory(history)"
              @close="removeSearchHistory(index)"
            >
              {{ formatSearchHistory(history) }}
            </NTag>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="search-actions">
          <NButton type="primary" @click="handleSearch">
            <TheIcon icon="material-symbols:search" :size="16" class="mr-1" />
            查询
          </NButton>
          <NButton @click="handleReset">
            <TheIcon icon="material-symbols:refresh" :size="16" class="mr-1" />
            重置
          </NButton>
          <NButton text @click="toggleAdvanced">
            {{ showAdvanced ? '收起' : '展开' }}高级搜索
            <TheIcon
              :icon="showAdvanced ? 'material-symbols:expand-less' : 'material-symbols:expand-more'"
              :size="16"
              class="ml-1"
            />
          </NButton>
          <NButton v-if="hasSearchConditions" text @click="saveCurrentSearch">
            <TheIcon icon="material-symbols:bookmark-add" :size="16" class="mr-1" />
            保存搜索
          </NButton>
        </div>
      </div>
    </NCard>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { NCard, NInput, NSelect, NDatePicker, NButton, NTag, useMessage } from 'naive-ui'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useRepairDictOptions } from '../composables/useRepairDictOptions'

const message = useMessage()

// Props
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({}),
  },
})

// Emits
const emit = defineEmits(['update:modelValue', 'search', 'reset'])

// 状态
const showAdvanced = ref(false)
const quickFilter = ref('')
const searchHistory = ref([])

// 搜索表单
const searchForm = reactive({
  device_number: '',
  applicant: '',
  brand: '',
  is_fault: null,
  repair_date_range: null,
  company: '',
  department: '',
  workshop: '',
  category: '',
  fault_reason: '',
  damage_category: '',
  repairer: '',
})

// 选项数据 - 使用字典数据
const {
  categoryOptions,
  brandOptions,
  faultReasonOptions,
  damageCategoryOptions,
} = useRepairDictOptions({ withAllOption: false })

// 故障状态选项（固定值，不需要字典）
const faultStatusOptions = ref([
  { label: '故障', value: true },
  { label: '正常维护', value: false },
])

// 计算属性
const hasSearchConditions = computed(() => {
  return Object.values(searchForm).some((value) => {
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return value !== '' && value !== null && value !== undefined
  })
})

// 方法
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value
}

const handleSearch = () => {
  // 保存搜索历史
  if (hasSearchConditions.value) {
    saveToHistory()
  }
  emit('search', { ...searchForm })
}

const handleReset = () => {
  Object.assign(searchForm, {
    device_number: '',
    applicant: '',
    brand: '',
    is_fault: null,
    repair_date_range: null,
    company: '',
    department: '',
    workshop: '',
    category: '',
    fault_reason: '',
    damage_category: '',
    repairer: '',
  })
  quickFilter.value = ''
  emit('reset')
}

const setQuickFilter = (type) => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  // 重置搜索条件
  handleReset()

  switch (type) {
    case 'today':
      searchForm.repair_date_range = [today.getTime(), now.getTime()]
      break
    case 'week':
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay())
      searchForm.repair_date_range = [weekStart.getTime(), now.getTime()]
      break
    case 'month':
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
      searchForm.repair_date_range = [monthStart.getTime(), now.getTime()]
      break
    case 'fault':
      searchForm.is_fault = true
      break
    case 'maintenance':
      searchForm.is_fault = false
      break
  }

  quickFilter.value = type
  handleSearch()
}

const saveCurrentSearch = () => {
  const searchName = prompt('请输入搜索条件名称：')
  if (searchName) {
    const searchCondition = {
      name: searchName,
      conditions: { ...searchForm },
      timestamp: Date.now(),
    }
    saveToHistory(searchCondition)
    message.success('搜索条件已保存')
  }
}

const saveToHistory = (customCondition = null) => {
  const condition = customCondition || {
    name: generateSearchName(),
    conditions: { ...searchForm },
    timestamp: Date.now(),
  }

  // 避免重复保存相同的搜索条件
  const exists = searchHistory.value.some(
    (item) => JSON.stringify(item.conditions) === JSON.stringify(condition.conditions)
  )

  if (!exists) {
    searchHistory.value.unshift(condition)
    // 限制历史记录数量
    if (searchHistory.value.length > 10) {
      searchHistory.value = searchHistory.value.slice(0, 10)
    }
    // 保存到本地存储
    localStorage.setItem('repair-search-history', JSON.stringify(searchHistory.value))
  }
}

const generateSearchName = () => {
  const conditions = []
  if (searchForm.device_number) conditions.push(`编号:${searchForm.device_number}`)
  if (searchForm.applicant) conditions.push(`申请人:${searchForm.applicant}`)
  if (searchForm.brand) conditions.push(`品牌:${searchForm.brand}`)
  if (searchForm.is_fault !== null) conditions.push(`状态:${searchForm.is_fault ? '故障' : '正常'}`)

  return conditions.length > 0 ? conditions.join(', ') : '搜索条件'
}

const formatSearchHistory = (history) => {
  return history.name
}

const applySearchHistory = (history) => {
  Object.assign(searchForm, history.conditions)
  handleSearch()
}

const removeSearchHistory = (index) => {
  searchHistory.value.splice(index, 1)
  localStorage.setItem('repair-search-history', JSON.stringify(searchHistory.value))
}

// 监听表单变化
watch(
  searchForm,
  (newValue) => {
    emit('update:modelValue', { ...newValue })
  },
  { deep: true }
)

// 监听props变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      Object.assign(searchForm, newValue)
    }
  },
  { immediate: true, deep: true }
)

// 初始化
onMounted(() => {
  // 加载搜索历史
  const savedHistory = localStorage.getItem('repair-search-history')
  if (savedHistory) {
    try {
      searchHistory.value = JSON.parse(savedHistory)
    } catch (error) {
      console.error('Failed to load search history:', error)
    }
  }
})
</script>

<style scoped>
.advanced-search {
  margin-bottom: 16px;
}

.search-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.advanced-row {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.search-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e6;
}

.quick-filters {
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 14px;
  color: #666;
  margin-right: 8px;
}

.search-history {
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
}

.history-group {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.history-label {
  font-size: 14px;
  color: #666;
  margin-right: 8px;
  line-height: 24px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .search-row {
    flex-direction: column;
    align-items: stretch;
  }

  .search-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group,
  .history-group {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* 动画效果 */
.advanced-row {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
