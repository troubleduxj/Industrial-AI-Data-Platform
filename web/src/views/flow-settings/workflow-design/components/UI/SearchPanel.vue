<template>
  <div class="search-panel" :class="{ collapsed: isCollapsed, floating: isFloating }">
    <!-- 面板头部 -->
    <div class="search-header">
      <div class="search-title">
        <span class="icon">🔍</span>
        <span class="title-text">搜索</span>
      </div>
      <div class="header-actions">
        <button
          class="action-btn"
          :title="isFloating ? '固定面板' : '浮动面板'"
          @click="toggleFloating"
        >
          <span class="icon">{{ isFloating ? '📌' : '🔗' }}</span>
        </button>
        <button
          class="action-btn"
          :title="isCollapsed ? '展开面板' : '收起面板'"
          @click="toggleCollapse"
        >
          <span class="icon">{{ isCollapsed ? '▼' : '▲' }}</span>
        </button>
        <button class="action-btn close-btn" title="关闭搜索面板" @click="handleClose">
          <span class="icon">✕</span>
        </button>
      </div>
    </div>

    <!-- 搜索内容 -->
    <div v-if="!isCollapsed" class="search-content">
      <!-- 搜索输入框 -->
      <div class="search-input-group">
        <div class="input-wrapper">
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="text"
            class="search-input"
            :placeholder="searchPlaceholder"
            @input="handleSearchInput"
            @keydown="handleKeyDown"
            @focus="handleInputFocus"
            @blur="handleInputBlur"
          />
          <button v-if="searchQuery" class="clear-btn" title="清空搜索" @click="clearSearch">
            <span class="icon">✕</span>
          </button>
        </div>
        <button
          class="search-btn"
          :disabled="!searchQuery.trim()"
          title="执行搜索"
          @click="performSearch"
        >
          <span class="icon">🔍</span>
        </button>
      </div>

      <!-- 搜索选项 -->
      <div class="search-options">
        <div class="option-group">
          <label class="option-label">
            <input
              v-model="searchOptions.caseSensitive"
              type="checkbox"
              @change="handleOptionChange"
            />
            <span>区分大小写</span>
          </label>
          <label class="option-label">
            <input v-model="searchOptions.wholeWord" type="checkbox" @change="handleOptionChange" />
            <span>全词匹配</span>
          </label>
          <label class="option-label">
            <input v-model="searchOptions.regex" type="checkbox" @change="handleOptionChange" />
            <span>正则表达式</span>
          </label>
        </div>
      </div>

      <!-- 搜索范围 -->
      <div class="search-scope">
        <div class="scope-title">搜索范围</div>
        <div class="scope-options">
          <label class="scope-option">
            <input v-model="searchScope.nodes" type="checkbox" @change="handleScopeChange" />
            <span>节点</span>
          </label>
          <label class="scope-option">
            <input v-model="searchScope.connections" type="checkbox" @change="handleScopeChange" />
            <span>连接</span>
          </label>
          <label class="scope-option">
            <input v-model="searchScope.properties" type="checkbox" @change="handleScopeChange" />
            <span>属性</span>
          </label>
          <label class="scope-option">
            <input v-model="searchScope.comments" type="checkbox" @change="handleScopeChange" />
            <span>注释</span>
          </label>
        </div>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0 || isSearching" class="search-results">
        <div class="results-header">
          <span class="results-count">
            {{ isSearching ? '搜索中...' : `找到 ${searchResults.length} 个结果` }}
          </span>
          <button
            v-if="searchResults.length > 0"
            class="clear-results-btn"
            title="清空结果"
            @click="clearResults"
          >
            <span class="icon">🗑️</span>
          </button>
        </div>

        <div v-if="!isSearching" class="results-list">
          <div
            v-for="(result, index) in searchResults"
            :key="index"
            class="result-item"
            :class="{ active: selectedResultIndex === index }"
            @click="selectResult(index)"
            @dblclick="navigateToResult(result)"
          >
            <div class="result-icon">
              <span class="icon">{{ getResultIcon(result.type) }}</span>
            </div>
            <div class="result-content">
              <div class="result-title">{{ result.title }}</div>
              <div class="result-description">{{ result.description }}</div>
              <div class="result-path">{{ result.path }}</div>
            </div>
            <div class="result-actions">
              <button class="action-btn" title="跳转到结果" @click.stop="navigateToResult(result)">
                <span class="icon">→</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="isSearching" class="loading-indicator">
          <div class="spinner"></div>
          <span>搜索中...</span>
        </div>
      </div>

      <!-- 无结果提示 -->
      <div v-if="hasSearched && searchResults.length === 0 && !isSearching" class="no-results">
        <div class="no-results-icon">🔍</div>
        <div class="no-results-text">未找到匹配的结果</div>
        <div class="no-results-suggestion">尝试调整搜索条件或扩大搜索范围</div>
      </div>
    </div>

    <!-- 快捷键提示 -->
    <div v-if="!isCollapsed && showShortcuts" class="search-shortcuts">
      <div class="shortcuts-title">快捷键</div>
      <div class="shortcut-item">
        <span class="shortcut-key">Ctrl+F</span>
        <span class="shortcut-desc">打开搜索</span>
      </div>
      <div class="shortcut-item">
        <span class="shortcut-key">Enter</span>
        <span class="shortcut-desc">搜索</span>
      </div>
      <div class="shortcut-item">
        <span class="shortcut-key">↑/↓</span>
        <span class="shortcut-desc">选择结果</span>
      </div>
      <div class="shortcut-item">
        <span class="shortcut-key">Esc</span>
        <span class="shortcut-desc">关闭</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SearchPanel',
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    initialQuery: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: '搜索节点、连接、属性...',
    },
    floating: {
      type: Boolean,
      default: false,
    },
    collapsed: {
      type: Boolean,
      default: false,
    },
    showShortcuts: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      isCollapsed: this.collapsed,
      isFloating: this.floating,
      searchQuery: this.initialQuery,
      searchOptions: {
        caseSensitive: false,
        wholeWord: false,
        regex: false,
      },
      searchScope: {
        nodes: true,
        connections: true,
        properties: true,
        comments: false,
      },
      searchResults: [],
      selectedResultIndex: -1,
      isSearching: false,
      hasSearched: false,
      searchTimeout: null,
    }
  },
  computed: {
    searchPlaceholder() {
      return this.placeholder
    },
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.focusSearchInput()
        })
      }
    },
    initialQuery(newVal) {
      this.searchQuery = newVal
    },
  },
  mounted() {
    if (this.visible) {
      this.focusSearchInput()
    }
  },
  methods: {
    // 切换折叠状态
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
      this.$emit('collapse-change', this.isCollapsed)
    },

    // 切换浮动状态
    toggleFloating() {
      this.isFloating = !this.isFloating
      this.$emit('floating-change', this.isFloating)
    },

    // 关闭面板
    handleClose() {
      this.$emit('close')
    },

    // 聚焦搜索输入框
    focusSearchInput() {
      if (this.$refs.searchInput) {
        this.$refs.searchInput.focus()
      }
    },

    // 处理搜索输入
    handleSearchInput() {
      // 防抖搜索
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }
      this.searchTimeout = setTimeout(() => {
        if (this.searchQuery.trim()) {
          this.performSearch()
        } else {
          this.clearResults()
        }
      }, 300)
    },

    // 处理键盘事件
    handleKeyDown(event) {
      switch (event.key) {
        case 'Enter':
          event.preventDefault()
          this.performSearch()
          break
        case 'Escape':
          event.preventDefault()
          this.handleClose()
          break
        case 'ArrowDown':
          event.preventDefault()
          this.selectNextResult()
          break
        case 'ArrowUp':
          event.preventDefault()
          this.selectPreviousResult()
          break
      }
    },

    // 输入框获得焦点
    handleInputFocus() {
      this.$emit('input-focus')
    },

    // 输入框失去焦点
    handleInputBlur() {
      this.$emit('input-blur')
    },

    // 清空搜索
    clearSearch() {
      this.searchQuery = ''
      this.clearResults()
      this.focusSearchInput()
    },

    // 执行搜索
    async performSearch() {
      if (!this.searchQuery.trim()) return

      this.isSearching = true
      this.hasSearched = true
      this.selectedResultIndex = -1

      try {
        const searchParams = {
          query: this.searchQuery,
          options: this.searchOptions,
          scope: this.searchScope,
        }

        this.$emit('search', searchParams)

        // 模拟搜索延迟
        await new Promise((resolve) => setTimeout(resolve, 500))

        // 这里应该调用实际的搜索逻辑
        this.searchResults = await this.executeSearch(searchParams)

        this.$emit('search-complete', {
          query: this.searchQuery,
          results: this.searchResults,
        })
      } catch (error) {
        console.error('搜索失败:', error)
        this.$emit('search-error', error)
      } finally {
        this.isSearching = false
      }
    },

    // 实际搜索逻辑（需要根据具体需求实现）
    async executeSearch(params) {
      // 这里应该实现实际的搜索逻辑
      // 返回搜索结果数组
      return []
    },

    // 处理选项变化
    handleOptionChange() {
      if (this.searchQuery.trim()) {
        this.performSearch()
      }
    },

    // 处理范围变化
    handleScopeChange() {
      if (this.searchQuery.trim()) {
        this.performSearch()
      }
    },

    // 清空结果
    clearResults() {
      this.searchResults = []
      this.selectedResultIndex = -1
      this.hasSearched = false
    },

    // 选择结果
    selectResult(index) {
      this.selectedResultIndex = index
      this.$emit('result-select', this.searchResults[index])
    },

    // 选择下一个结果
    selectNextResult() {
      if (this.searchResults.length === 0) return
      this.selectedResultIndex = Math.min(
        this.selectedResultIndex + 1,
        this.searchResults.length - 1
      )
      this.$emit('result-select', this.searchResults[this.selectedResultIndex])
    },

    // 选择上一个结果
    selectPreviousResult() {
      if (this.searchResults.length === 0) return
      this.selectedResultIndex = Math.max(this.selectedResultIndex - 1, 0)
      this.$emit('result-select', this.searchResults[this.selectedResultIndex])
    },

    // 导航到结果
    navigateToResult(result) {
      this.$emit('navigate-to-result', result)
    },

    // 获取结果图标
    getResultIcon(type) {
      const icons = {
        node: '🔵',
        connection: '🔗',
        property: '⚙️',
        comment: '💬',
      }
      return icons[type] || '📄'
    },
  },
}
</script>

<style scoped>
.search-panel {
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  max-width: 400px;
  max-height: 600px;
  display: flex;
  flex-direction: column;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: all 0.3s ease;
}

.search-panel.collapsed {
  max-height: 40px;
}

.search-panel.floating {
  position: fixed;
  top: 100px;
  right: 20px;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

/* 头部样式 */
.search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--header-bg, #f5f5f5);
  border-bottom: 1px solid var(--border-color, #e0e0e0);
  border-radius: 8px 8px 0 0;
}

.search-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: var(--text-color, #333333);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: none;
  border: none;
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--hover-bg, #e0e0e0);
  color: var(--text-color, #333333);
}

.close-btn:hover {
  background: #ff4757;
  color: white;
}

/* 内容样式 */
.search-content {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
}

/* 搜索输入组 */
.search-input-group {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 8px 32px 8px 12px;
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  border-color: var(--primary-color, #007bff);
}

.clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
  padding: 2px;
}

.search-btn {
  padding: 8px 12px;
  background: var(--primary-color, #007bff);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.search-btn:disabled {
  background: var(--disabled-bg, #cccccc);
  cursor: not-allowed;
}

.search-btn:not(:disabled):hover {
  background: var(--primary-color-dark, #0056b3);
}

/* 搜索选项 */
.search-options {
  margin-bottom: 12px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-color-secondary, #666666);
  cursor: pointer;
}

/* 搜索范围 */
.search-scope {
  margin-bottom: 12px;
}

.scope-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color, #333333);
  margin-bottom: 6px;
}

.scope-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.scope-option {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-color-secondary, #666666);
  cursor: pointer;
}

/* 搜索结果 */
.search-results {
  border-top: 1px solid var(--border-color, #e0e0e0);
  padding-top: 12px;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.results-count {
  font-size: 13px;
  color: var(--text-color-secondary, #666666);
}

.clear-results-btn {
  background: none;
  border: none;
  padding: 4px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-color-secondary, #666666);
}

.clear-results-btn:hover {
  background: var(--hover-bg, #e0e0e0);
}

.results-list {
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.result-item:hover,
.result-item.active {
  background: var(--hover-bg, #f0f0f0);
}

.result-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color, #333333);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-description {
  font-size: 12px;
  color: var(--text-color-secondary, #666666);
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-path {
  font-size: 11px;
  color: var(--text-color-tertiary, #999999);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-actions {
  flex-shrink: 0;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-color-secondary, #666666);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color, #e0e0e0);
  border-top: 2px solid var(--primary-color, #007bff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 无结果提示 */
.no-results {
  text-align: center;
  padding: 20px;
  color: var(--text-color-secondary, #666666);
}

.no-results-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.no-results-text {
  font-size: 14px;
  margin-bottom: 4px;
}

.no-results-suggestion {
  font-size: 12px;
  color: var(--text-color-tertiary, #999999);
}

/* 快捷键提示 */
.search-shortcuts {
  border-top: 1px solid var(--border-color, #e0e0e0);
  padding: 8px 12px;
  background: var(--bg-secondary, #f9f9f9);
}

.shortcuts-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color, #333333);
  margin-bottom: 6px;
}

.shortcut-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-color-secondary, #666666);
  margin-bottom: 2px;
}

.shortcut-key {
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 3px;
  padding: 2px 4px;
  font-family: monospace;
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .search-panel {
    --bg-color: #2d2d2d;
    --bg-secondary: #3d3d3d;
    --header-bg: #3d3d3d;
    --border-color: #4d4d4d;
    --text-color: #ffffff;
    --text-color-secondary: #cccccc;
    --text-color-tertiary: #999999;
    --hover-bg: #4d4d4d;
    --primary-color: #0084ff;
    --primary-color-dark: #0066cc;
    --disabled-bg: #555555;
  }
}
</style>
