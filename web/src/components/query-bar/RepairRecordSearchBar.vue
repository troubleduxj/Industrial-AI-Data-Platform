<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import { NButton, NCard, NInput, NSelect, NDatePicker, NTag, useMessage } from 'naive-ui'
import QueryBarItem from '@/components/page/QueryBarItem.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

const message = useMessage()

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  brandOptions: {
    type: Array,
    default: () => [
      { label: '全部品牌', value: '' },
      { label: '松下', value: '松下' },
      { label: '林肯', value: '林肯' },
      { label: '米勒', value: '米勒' },
      { label: '奥太', value: '奥太' },
      { label: '瑞凌', value: '瑞凌' },
    ],
  },
  categoryOptions: {
    type: Array,
    default: () => [
      { label: '全部类别', value: '' },
      { label: '二氧化碳保护焊机', value: '二氧化碳保护焊机' },
      { label: '氩弧焊机', value: '氩弧焊机' },
      { label: '电焊机', value: '电焊机' },
      { label: '等离子切割机', value: '等离子切割机' },
    ],
  },
  faultStatusOptions: {
    type: Array,
    default: () => [
      { label: '全部状态', value: null },
      { label: '故障', value: true },
      { label: '正常维护', value: false },
    ],
  },
  faultReasonOptions: {
    type: Array,
    default: () => [
      { label: '全部原因', value: '' },
      { label: '操作不当', value: '操作不当' },
      { label: '老化磨损', value: '老化磨损' },
      { label: '环境因素', value: '环境因素' },
      { label: '设备缺陷', value: '设备缺陷' },
      { label: '维护不当', value: '维护不当' },
    ],
  },
  damageCategoryOptions: {
    type: Array,
    default: () => [
      { label: '全部类别', value: '' },
      { label: '正常损坏', value: '正常损坏' },
      { label: '非正常损坏', value: '非正常损坏' },
      { label: '人为损坏', value: '人为损坏' },
    ],
  },
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

// 状态
const showAdvanced = ref(false)
const quickFilter = ref('')
const searchHistory = ref([])

// 计算属性
const hasSearchConditions = computed(() => {
  return Object.values(props.modelValue).some((value) => {
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return value !== '' && value !== null && value !== undefined
  })
})

const handleSearch = () => {
  const searchParams = {
    device_number: props.modelValue.device_number?.trim(),
    applicant: props.modelValue.applicant?.trim(),
    brand: props.modelValue.brand,
    category: props.modelValue.category,
    is_fault: props.modelValue.is_fault,
    repair_date_range: props.modelValue.repair_date_range,
    company: props.modelValue.company?.trim(),
    department: props.modelValue.department?.trim(),
    workshop: props.modelValue.workshop?.trim(),
    repairer: props.modelValue.repairer?.trim(),
    fault_reason: props.modelValue.fault_reason,
    damage_category: props.modelValue.damage_category,
    construction_unit: props.modelValue.construction_unit?.trim(),
    phone: props.modelValue.phone?.trim(),
  }

  // 过滤掉空值
  const filteredParams = Object.fromEntries(
    Object.entries(searchParams).filter(([_, v]) => v !== undefined && v !== '' && v !== null)
  )

  // 保存搜索历史
  if (hasSearchConditions.value) {
    saveToHistory()
  }

  console.log('维修记录搜索参数:', filteredParams)
  emit('search', filteredParams)
}

const handleReset = () => {
  const emptyValues = {
    device_number: '',
    applicant: '',
    brand: '',
    category: '',
    is_fault: null,
    repair_date_range: null,
    company: '',
    department: '',
    workshop: '',
    repairer: '',
    fault_reason: '',
    damage_category: '',
    construction_unit: '',
    phone: '',
  }
  quickFilter.value = ''
  emit('update:modelValue', emptyValues)
  emit('reset')
  // 确保UI更新
  nextTick(() => {
    emit('update:modelValue', emptyValues)
  })
}

const updateValue = (key, value) => {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}

// 高级查询功能
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value
}

const setQuickFilter = (type) => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  // 重置搜索条件
  handleReset()

  switch (type) {
    case 'today':
      updateValue('repair_date_range', [today.getTime(), now.getTime()])
      break
    case 'week':
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay())
      updateValue('repair_date_range', [weekStart.getTime(), now.getTime()])
      break
    case 'month':
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
      updateValue('repair_date_range', [monthStart.getTime(), now.getTime()])
      break
    case 'fault':
      updateValue('is_fault', true)
      break
    case 'maintenance':
      updateValue('is_fault', false)
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
      conditions: { ...props.modelValue },
      timestamp: Date.now(),
    }
    saveToHistory(searchCondition)
    message.success('搜索条件已保存')
  }
}

const saveToHistory = (customCondition = null) => {
  const condition = customCondition || {
    name: generateSearchName(),
    conditions: { ...props.modelValue },
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
  if (props.modelValue.device_number) conditions.push(`编号:${props.modelValue.device_number}`)
  if (props.modelValue.applicant) conditions.push(`申请人:${props.modelValue.applicant}`)
  if (props.modelValue.brand) conditions.push(`品牌:${props.modelValue.brand}`)
  if (props.modelValue.is_fault !== null)
    conditions.push(`状态:${props.modelValue.is_fault ? '故障' : '正常'}`)

  return conditions.length > 0 ? conditions.join(', ') : '搜索条件'
}

const formatSearchHistory = (history) => {
  return history.name
}

const applySearchHistory = (history) => {
  emit('update:modelValue', { ...history.conditions })
  handleSearch()
}

const removeSearchHistory = (index) => {
  searchHistory.value.splice(index, 1)
  localStorage.setItem('repair-search-history', JSON.stringify(searchHistory.value))
}

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

<template>
  <NCard class="mb-15" rounded-10>
    <div class="search-container">
      <!-- 基础搜索行 -->
      <div flex flex-wrap items-center gap-15>
        <QueryBarItem label="焊机编号" :label-width="70">
          <NInput
            :value="modelValue.device_number"
            clearable
            type="text"
            placeholder="请输入焊机编号"
            @update:value="(val) => updateValue('device_number', val)"
            @keypress.enter="handleSearch"
          />
        </QueryBarItem>
        <QueryBarItem label="申请人" :label-width="70">
          <NInput
            :value="modelValue.applicant"
            clearable
            type="text"
            placeholder="请输入申请人"
            @update:value="(val) => updateValue('applicant', val)"
            @keypress.enter="handleSearch"
          />
        </QueryBarItem>
        <QueryBarItem label="设备品牌" :label-width="70">
          <NSelect
            :value="modelValue.brand"
            style="width: 150px"
            :options="props.brandOptions"
            clearable
            placeholder="请选择品牌"
            @update:value="(val) => updateValue('brand', val)"
          />
        </QueryBarItem>
        <QueryBarItem label="故障状态" :label-width="70">
          <NSelect
            :value="modelValue.is_fault"
            style="width: 150px"
            :options="props.faultStatusOptions"
            clearable
            placeholder="请选择状态"
            @update:value="(val) => updateValue('is_fault', val)"
          />
        </QueryBarItem>
        <QueryBarItem label="报修日期" :label-width="70">
          <NDatePicker
            :value="modelValue.repair_date_range"
            type="daterange"
            placeholder="请选择日期范围"
            style="width: 300px"
            @update:value="(val) => updateValue('repair_date_range', val)"
          />
        </QueryBarItem>
      </div>

      <!-- 高级搜索行 -->
      <div v-show="showAdvanced" class="search-row advanced-row">
        <div flex flex-wrap items-center gap-15>
          <QueryBarItem label="设备类别" :label-width="70">
            <NSelect
              :value="modelValue.category"
              style="width: 180px"
              :options="props.categoryOptions"
              clearable
              placeholder="请选择设备类别"
              @update:value="(val) => updateValue('category', val)"
            />
          </QueryBarItem>
          <QueryBarItem label="公司" :label-width="70">
            <NInput
              :value="modelValue.company"
              clearable
              type="text"
              placeholder="请输入公司名称"
              @update:value="(val) => updateValue('company', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
          <QueryBarItem label="部门" :label-width="70">
            <NInput
              :value="modelValue.department"
              clearable
              type="text"
              placeholder="请输入部门"
              @update:value="(val) => updateValue('department', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
          <QueryBarItem label="车间" :label-width="70">
            <NInput
              :value="modelValue.workshop"
              clearable
              type="text"
              placeholder="请输入车间"
              @update:value="(val) => updateValue('workshop', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
          <QueryBarItem label="施工单位" :label-width="70">
            <NInput
              :value="modelValue.construction_unit"
              clearable
              type="text"
              placeholder="请输入施工单位"
              @update:value="(val) => updateValue('construction_unit', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
        </div>
      </div>

      <!-- 更多高级搜索选项 -->
      <div v-show="showAdvanced" class="search-row advanced-row">
        <div flex flex-wrap items-center gap-15>
          <QueryBarItem label="故障原因" :label-width="70">
            <NSelect
              :value="modelValue.fault_reason"
              style="width: 150px"
              :options="props.faultReasonOptions"
              clearable
              placeholder="请选择故障原因"
              @update:value="(val) => updateValue('fault_reason', val)"
            />
          </QueryBarItem>
          <QueryBarItem label="损坏类别" :label-width="70">
            <NSelect
              :value="modelValue.damage_category"
              style="width: 150px"
              :options="props.damageCategoryOptions"
              clearable
              placeholder="请选择损坏类别"
              @update:value="(val) => updateValue('damage_category', val)"
            />
          </QueryBarItem>
          <QueryBarItem label="维修人" :label-width="70">
            <NInput
              :value="modelValue.repairer"
              clearable
              type="text"
              placeholder="请输入维修人"
              @update:value="(val) => updateValue('repairer', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
          <QueryBarItem label="联系电话" :label-width="70">
            <NInput
              :value="modelValue.phone"
              clearable
              type="text"
              placeholder="请输入联系电话"
              @update:value="(val) => updateValue('phone', val)"
              @keypress.enter="handleSearch"
            />
          </QueryBarItem>
        </div>
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
          <TheIcon icon="material-symbols:search" :size="16" class="mr-5" />查询
        </NButton>
        <NButton @click="handleReset">
          <TheIcon icon="material-symbols:refresh" :size="16" class="mr-5" />重置
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
          <TheIcon icon="material-symbols:bookmark-add" :size="16" class="mr-5" />
          保存搜索
        </NButton>
      </div>
    </div>
  </NCard>
</template>

<style scoped>
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
  animation: slideDown 0.3s ease-out;
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

[flex~='wrap'] {
  flex-wrap: wrap;
}
</style>
