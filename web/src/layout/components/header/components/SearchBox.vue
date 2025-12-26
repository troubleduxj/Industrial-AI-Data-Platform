<template>
  <div class="search-box">
    <n-input
      ref="searchInputRef"
      v-model:value="searchQuery"
      :placeholder="placeholder + ' (Ctrl+K)'"
      clearable
      size="medium"
      class="search-input"
      @keyup.enter="handleSearch"
      @clear="handleClear"
      @focus="showSuggestions = true"
    >
      <template #prefix>
        <n-icon :component="SearchIcon" />
      </template>
      <template #suffix>
        <n-button v-if="searchQuery" text size="small" class="search-btn" @click="handleSearch">
          搜索
        </n-button>
      </template>
    </n-input>

    <!-- 搜索建议下拉框 -->
    <div v-if="showSuggestions && suggestions.length > 0" class="search-suggestions">
      <div
        v-for="(suggestion, index) in suggestions"
        :key="index"
        class="suggestion-item"
        @click="selectSuggestion(suggestion)"
      >
        <n-icon class="suggestion-icon">
          <component :is="getIconComponent(suggestion.icon)" />
        </n-icon>
        <div class="suggestion-content">
          <span class="suggestion-text">{{ suggestion.title }}</span>
          <span class="suggestion-description">{{ suggestion.description }}</span>
        </div>
        <span class="suggestion-type">{{ suggestion.type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { NInput, NIcon, NButton, useMessage } from 'naive-ui'
import {
  SearchOutline as SearchIcon,
  DocumentTextOutline,
  SettingsOutline,
  PeopleOutline,
  BarChartOutline,
  LanguageOutline,
} from '@vicons/ionicons5'
import { useThemeStore } from '@/store'

// Props
const props = defineProps({
  placeholder: {
    type: String,
    default: '搜索功能、页面、设置...',
  },
  maxSuggestions: {
    type: Number,
    default: 8,
  },
})

// Emits
const emit = defineEmits(['search', 'select'])

// Router
const router = useRouter()
const message = useMessage()
const themeStore = useThemeStore()

// 响应式数据
const searchQuery = ref('')
const showSuggestions = ref(false)
const searchInputRef = ref(null)

// 搜索建议数据
const searchSuggestions = [
  {
    title: '工作台',
    description: '查看系统概览和统计信息',
    path: '/workbench',
    icon: 'BarChartOutline',
    type: 'route',
  },
  {
    title: '个人资料',
    description: '查看和编辑个人信息',
    path: '/profile',
    icon: 'PeopleOutline',
    type: 'route',
  },
  {
    title: '主题设置',
    description: '切换应用主题色',
    action: 'theme',
    icon: 'SettingsOutline',
    type: 'action',
  },
  {
    title: '语言设置',
    description: '切换界面语言',
    action: 'language',
    icon: 'LanguageOutline',
    type: 'action',
  },
]

// 计算过滤后的建议
const suggestions = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()

  // 如果没有搜索内容，显示所有建议
  if (!query) {
    return searchSuggestions.slice(0, props.maxSuggestions)
  }

  // 有搜索内容时，显示过滤后的建议
  return searchSuggestions
    .filter(
      (item) =>
        item.title.toLowerCase().includes(query) ||
        item.description.toLowerCase().includes(query) ||
        item.type.toLowerCase().includes(query)
    )
    .slice(0, props.maxSuggestions)
})

// 监听搜索输入
watch(searchQuery, (newValue) => {
  // 如果有输入内容，显示过滤后的建议
  // 如果没有输入内容但搜索框已聚焦，显示所有建议
  if (newValue.trim().length > 0) {
    showSuggestions.value = true
  }
})

// 处理搜索
const handleSearch = () => {
  if (!searchQuery.value.trim()) return

  // 如果有完全匹配的建议，直接选择
  const exactMatch = suggestions.value.find(
    (item) => item.title.toLowerCase() === searchQuery.value.toLowerCase()
  )

  if (exactMatch) {
    selectSuggestion(exactMatch)
  } else {
    // 发出搜索事件
    emit('search', searchQuery.value)
    showSuggestions.value = false
  }
}

// 处理清空
const handleClear = () => {
  searchQuery.value = ''
  showSuggestions.value = false
  emit('search', '')
}

// 选择建议项
const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion.title
  showSuggestions.value = false

  // 发出选择事件
  emit('select', suggestion)

  // 根据建议类型执行相应操作
  if (suggestion.path) {
    router.push(suggestion.path)
  } else if (suggestion.action) {
    handleAction(suggestion.action)
  }
}

// 处理键盘快捷键
const handleKeydown = (event) => {
  // Ctrl+K 打开搜索框
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    focusSearch()
  }
  // ESC 关闭搜索框
  if (event.key === 'Escape') {
    closeSearch()
  }
}

// 聚焦搜索框
const focusSearch = () => {
  showSuggestions.value = true
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

// 关闭搜索框
const closeSearch = () => {
  showSuggestions.value = false
  searchQuery.value = ''
}

// 获取图标组件
const getIconComponent = (iconName) => {
  const iconMap = {
    BarChartOutline: BarChartOutline,
    PeopleOutline: PeopleOutline,
    LanguageOutline: LanguageOutline,
    DocumentTextOutline: DocumentTextOutline,
    SettingsOutline: SettingsOutline,
  }
  return iconMap[iconName] || DocumentTextOutline
}

// 处理特殊操作
const handleAction = (action) => {
  switch (action) {
    case 'theme':
      // 触发主题设置
      console.log('打开主题设置')
      break
    case 'language':
      // 触发语言设置
      console.log('打开语言设置')
      break
    default:
      console.log('未知操作:', action)
  }
}

// 点击外部关闭建议
const handleClickOutside = (event) => {
  if (!event.target.closest('.search-box')) {
    showSuggestions.value = false
  }
}

// 生命周期
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.search-box {
  position: relative;
  width: 300px;
  max-width: 100%;
}

.search-input {
  width: 100%;

  :deep(.n-input) {
    border-radius: 10px;
    background-color: var(--input-color, #eeeeee);
    border: 1px solid transparent;
    transition: all 0.2s ease;

    &:hover {
      border-color: var(--primary-color, #f4511e);
      background-color: var(--input-color-hover, #fff);
    }

    &:focus-within {
      border-color: var(--primary-color, #f4511e);
      background-color: var(--input-color-focus, #fff);
      box-shadow: 0 0 0 2px var(--primary-color-suppl, rgba(244, 81, 30, 0.2));
    }
  }

  :deep(.n-input__input) {
    color: var(--text-color, #222222) !important;
  }

  :deep(.n-input__placeholder) {
    color: var(--placeholder-color, #666666) !important;
  }
}

.search-btn {
  color: var(--primary-color);
  font-size: 12px;
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 4px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-bottom: 1px solid var(--border-color, #f0f0f0);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.active {
  background-color: var(--hover-color, #f5f5f5);
}

.suggestion-icon {
  margin-right: 12px;
  color: var(--primary-color, #f4511e);
  font-size: 16px;
}

.suggestion-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.suggestion-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color, #333);
  margin-bottom: 2px;
}

.suggestion-description {
  font-size: 12px;
  color: var(--text-color-secondary, #999);
  line-height: 1.4;
}

.suggestion-type {
  font-size: 11px;
  color: var(--text-color-secondary, #999);
  background: var(--tag-bg, #f0f0f0);
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 深色主题适配 */
.dark .search-suggestions {
  background: var(--bg-color-dark, #2d2d30);
  border-color: var(--border-color-dark, #404040);
}

.dark .suggestion-item:hover {
  background-color: var(--hover-color-dark, #3a3a3a);
}

.dark .suggestion-text {
  color: var(--text-color-dark, #fff);
}

.dark .suggestion-type {
  background: var(--tag-bg-dark, #404040);
  color: var(--text-color-secondary-dark, #ccc);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-box {
    width: 200px;
  }
}

@media (max-width: 480px) {
  .search-box {
    width: 150px;
  }

  .search-input {
    font-size: 14px;
  }
}
</style>
