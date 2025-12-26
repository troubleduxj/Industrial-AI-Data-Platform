# 统一状态管理系统

本项目实现了一套完整的统一状态管理系统，基于 Pinia 构建，提供了模块化、类型安全、高性能的状态管理解决方案。

## 架构概览

### 核心模块

```
src/store/
├── index.js                 # 主入口文件
├── unified-state.js          # 统一状态管理核心
├── modules/                  # 状态模块
│   ├── index.js             # 模块导出

│   ├── ui-state.js          # UI界面状态
│   ├── app/                 # 应用状态
│   ├── user/                # 用户状态
│   ├── permission/          # 权限状态
│   ├── tags/                # 标签状态
│   └── chatWidget.js        # 聊天组件状态
└── README.md                # 本文档
```

### 状态模块说明



#### 4. UI界面状态 (`ui-state.js`)
- **功能**: 管理界面布局、主题、用户偏好、交互状态
- **主要状态**: 布局设置、主题配置、页面状态、模态框状态、表格状态、表单状态
- **核心方法**: toggleSidebar, setThemeMode, openModal, setCurrentPage, addTab

## 使用方法

### 1. 基础使用

```javascript
// 在组件中使用统一状态管理
import { useUnifiedState } from '@/composables/useUnifiedState'

export default {
  setup() {
    const { stores, stateManager } = useUnifiedState()
    
    // 访问特定store
    const collectorStore = stores.collector
    const uiStore = stores.ui
    
    return {
      collectorStore,
      uiStore
    }
  }
}
```

### 2. 使用应用状态

```javascript
import { useAppState } from '@/composables/useUnifiedState'

export default {
  setup() {
    const {
      appConfig,
      currentUser,
      loading,
      fetchAppConfig,
      updateConfig,
      initializeApp
    } = useAppState()
    
    // 获取应用配置
    const loadConfig = async () => {
      await fetchAppConfig()
    }
    
    // 初始化应用
    const handleInit = async () => {
      await initializeApp()
    }
    
    return {
      appConfig,
      currentUser,
      loading,
      loadConfig,
      handleInit
    }
  }
}
```

### 3. 使用UI状态

```javascript
import { useUIState } from '@/composables/useUnifiedState'

export default {
  setup() {
    const {
      sidebarCollapsed,
      isDarkMode,
      isMobile,
      toggleSidebar,
      setThemeMode,
      openModal
    } = useUIState()
    
    // 切换侧边栏
    const handleToggleSidebar = () => {
      toggleSidebar()
    }
    
    // 切换主题
    const handleThemeChange = (mode) => {
      setThemeMode(mode)
    }
    
    return {
      sidebarCollapsed,
      isDarkMode,
      isMobile,
      handleToggleSidebar,
      handleThemeChange
    }
  }
}
```

### 4. 状态同步

```javascript
import { useStateSync } from '@/composables/useUnifiedState'

export default {
  setup() {
    // 设置状态同步监听
    useStateSync({
      watchUIChanges: true,
      onUIChange: (newTheme, oldTheme) => {
        console.log('主题变化:', newTheme)
      }
    })
    
    return {}
  }
}
```

### 5. 状态持久化

```javascript
import { useStatePersistence } from '@/composables/useUnifiedState'

export default {
  setup() {
    const {
      saveToLocal,
      loadFromLocal,
      exportToFile,
      importFromFile
    } = useStatePersistence()
    
    // 保存状态到本地
    const handleSave = async () => {
      await saveToLocal('my-app-state')
    }
    
    // 从本地加载状态
    const handleLoad = async () => {
      await loadFromLocal('my-app-state')
    }
    
    // 导出状态到文件
    const handleExport = () => {
      exportToFile('app-backup.json')
    }
    
    return {
      handleSave,
      handleLoad,
      handleExport
    }
  }
}
```

## 高级特性

### 1. 状态同步机制

统一状态管理系统实现了自动的状态同步机制：

- **UI状态同步**: UI状态变化自动同步到相关组件
- **主题变更同步**: 主题配置保存后自动应用到全局
- **用户偏好同步**: 用户偏好变化自动更新界面设置

### 2. 错误处理

系统提供了全局错误处理机制：

- **全局错误捕获**: 自动捕获并显示系统错误
- **Promise错误处理**: 处理未捕获的异步错误
- **用户友好提示**: 将技术错误转换为用户可理解的提示

### 3. 性能优化

- **懒加载**: 状态模块按需加载
- **内存管理**: 自动清理过期数据
- **WebSocket优化**: 智能重连和消息处理
- **缓存策略**: 合理的数据缓存机制

### 4. 开发工具

```javascript
import { useStateDebug } from '@/composables/useUnifiedState'

const {
  logCurrentState,
  startStateMonitoring,
  analyzePerformance,
  resetStore
} = useStateDebug()

// 打印当前状态
logCurrentState()

// 开始状态监控
startStateMonitoring()

// 性能分析
analyzePerformance()

// 重置特定store
resetStore('ui')
```

## 最佳实践

### 1. 状态设计原则

- **单一职责**: 每个store只负责特定领域的状态
- **最小化状态**: 只存储必要的状态，派生状态使用getters
- **不可变性**: 避免直接修改状态，使用actions进行状态变更
- **类型安全**: 使用TypeScript或JSDoc提供类型提示

### 2. 性能优化建议

- **合理使用computed**: 对于复杂计算使用computed缓存结果
- **避免深度监听**: 只在必要时使用deep watch
- **及时清理**: 组件卸载时清理监听器和定时器
- **分页加载**: 大量数据使用分页或虚拟滚动

### 3. 错误处理策略

- **优雅降级**: 状态加载失败时提供默认值
- **用户提示**: 及时向用户反馈操作结果
- **错误恢复**: 提供重试机制和错误恢复选项
- **日志记录**: 记录关键操作和错误信息

### 4. 测试建议

```javascript
// 测试store的actions
import { setActivePinia, createPinia } from 'pinia'
// 其他业务模块的store导入

describe('UIStateStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should update theme', async () => {
    const store = useUIStateStore()
    store.setTheme('dark')
    expect(store.theme.mode).toBe('dark')
  })
})
```

## 迁移指南

### 从旧状态管理迁移

1. **识别现有状态**: 分析当前组件中的状态使用
2. **映射到新store**: 将状态映射到对应的统一状态模块
3. **更新组件**: 使用新的composable函数替换旧的状态访问
4. **测试验证**: 确保功能正常且性能良好

### 示例迁移

```javascript
// 旧方式
export default {
  data() {
    return {
      theme: 'light',
      loading: false
    }
  },
  mounted() {
    this.loadTheme()
  }
}

// 新方式
import { useUIState } from '@/composables/useUnifiedState'

export default {
  setup() {
    const { theme, setThemeMode } = useUIState()
    
    onMounted(() => {
      setThemeMode('light')
    })
    
    return {
      theme
    }
  }
}
```

## 故障排除

### 常见问题

1. **状态不更新**: 检查是否正确使用reactive/ref包装
2. **内存泄漏**: 确保组件卸载时清理监听器
3. **性能问题**: 使用开发工具分析状态大小和变更频率
4. **同步问题**: 检查状态同步配置和网络连接

### 调试技巧

```javascript
// 启用详细日志
if (import.meta.env.DEV) {
  const { startStateMonitoring } = useStateDebug()
  startStateMonitoring()
}

// 检查状态快照
console.log('当前状态:', unifiedStateManager.getStateSnapshot())

// 分析性能
const { analyzePerformance } = useStateDebug()
analyzePerformance()
```

## 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ 实现统一状态管理核心功能
- ✨ 添加采集器、配置、监控、UI状态模块
- ✨ 提供完整的composable函数库
- ✨ 实现状态同步和持久化机制
- ✨ 添加开发工具和调试功能

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。