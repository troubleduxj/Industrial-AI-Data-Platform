# 通用组件库

本目录包含项目中可复用的通用组件，这些组件不包含具体业务逻辑，可以在不同的业务场景中使用。

## 组件列表

### AppProvider
应用程序配置提供者组件，用于全局配置Naive UI主题、国际化等设置。

**功能特性:**
- 主题配置管理
- 国际化支持
- 全局组件提供者

**使用示例:**
```vue
<template>
  <AppProvider>
    <router-view />
  </AppProvider>
</template>
```

### LoadingEmptyWrapper
加载和空状态包装器组件，提供统一的加载、空数据和网络错误状态展示。

**功能特性:**
- 加载状态展示
- 空数据状态展示
- 网络错误状态展示
- 自定义图标和文本
- 重试功能

**使用示例:**
```vue
<template>
  <LoadingEmptyWrapper
    :loading="isLoading"
    :empty="isEmpty"
    empty-description="暂无数据"
    :show-network-reload="true"
    @reload="handleReload"
  >
    <YourContent />
  </LoadingEmptyWrapper>
</template>
```

### PermissionButton
权限按钮组件，根据用户权限自动显示/隐藏或禁用按钮。

**功能特性:**
- 基于权限的显示控制
- 基于角色的访问控制
- 支持API权限和按钮权限
- 继承Naive UI Button的所有属性

**使用示例:**
```vue
<template>
  <PermissionButton
    permission="user:create"
    type="primary"
    @click="handleCreate"
  >
    创建用户
  </PermissionButton>
</template>
```

### ScrollX
水平滚动组件，提供平滑的水平滚动功能。

**功能特性:**
- 鼠标滚轮支持
- 滚动箭头按钮
- 滚动指示器
- 平滑滚动动画
- 响应式设计

**使用示例:**
```vue
<template>
  <ScrollX :show-arrows="true" :show-indicator="true">
    <div class="flex gap-4">
      <div v-for="item in items" :key="item.id">{{ item.name }}</div>
    </div>
  </ScrollX>
</template>
```

### ViewToggle
视图切换组件，提供统一的视图模式切换功能。

**功能特性:**
- 多种预定义视图选项
- 自定义视图选项
- 图标和文本显示
- 紧凑模式支持
- 响应式设计

**使用示例:**
```vue
<template>
  <ViewToggle
    v-model="currentView"
    :options="viewOptions"
    :show-label="true"
    @change="handleViewChange"
  />
</template>

<script setup>
import { TABLE_CARD_OPTIONS } from '@/components/common/view-toggle-options'

const currentView = ref('table')
const viewOptions = TABLE_CARD_OPTIONS
</script>
```

## 视图切换选项配置

`view-toggle-options.js` 文件提供了预定义的视图切换选项配置：

- `TABLE_CARD_OPTIONS` - 表格和卡片视图
- `CHART_TABLE_OPTIONS` - 图表和表格视图
- `DEVICE_VIEW_OPTIONS` - 设备监控视图（卡片、表格、列表）
- `STATISTICS_VIEW_OPTIONS` - 统计数据视图
- `FILE_VIEW_OPTIONS` - 文件管理视图
- `CALENDAR_VIEW_OPTIONS` - 日历视图
- `MAP_VIEW_OPTIONS` - 地图视图

## TypeScript 支持

所有组件都提供了完整的TypeScript类型定义，位于 `types.ts` 文件中。

```typescript
import type { 
  LoadingEmptyWrapperProps,
  ScrollXProps,
  ViewToggleProps,
  PermissionButtonProps 
} from '@/components/common/types'
```

## 组件安装

### 按需引入
```javascript
import { LoadingEmptyWrapper, ScrollX, ViewToggle } from '@/components/common'
```

### 全局注册
```javascript
import { installCommonComponents } from '@/components/common'

const app = createApp(App)
installCommonComponents(app)
```

## 开发规范

### 组件开发原则
1. **通用性** - 组件应该具有通用性，不包含具体业务逻辑
2. **可配置** - 提供丰富的配置选项，满足不同使用场景
3. **可扩展** - 支持插槽和事件，允许用户自定义内容和行为
4. **无障碍** - 支持键盘导航和屏幕阅读器
5. **响应式** - 适配不同屏幕尺寸

### 命名规范
- 组件文件使用PascalCase命名
- Props使用camelCase命名
- 事件使用kebab-case命名
- CSS类使用BEM命名方法论

### 文档要求
- 每个组件都应该有详细的JSDoc注释
- 提供完整的使用示例
- 说明所有Props、Events和Slots
- 包含TypeScript类型定义

### 测试要求
- 为每个组件编写单元测试
- 测试组件的Props、Events和Slots
- 测试组件的交互行为和边界情况

## 性能优化

### 懒加载
大部分组件支持异步加载，可以通过动态导入减少初始包大小：

```javascript
const ScrollX = defineAsyncComponent(() => import('@/components/common/ScrollX.vue'))
```

### 缓存优化
- 使用computed缓存计算结果
- 合理使用v-memo指令
- 避免不必要的重新渲染

### 内存管理
- 及时清理事件监听器
- 使用ResizeObserver监听尺寸变化
- 避免内存泄漏

## 主题定制

所有组件都支持CSS变量进行主题定制：

```css
:root {
  --primary-color: #18a058;
  --bg-color: #fff;
  --border-color: #e0e0e6;
  --text-color: #333;
  --text-color-secondary: #666;
}

.dark {
  --bg-color: #18181c;
  --border-color: #48484e;
  --text-color: #fff;
  --text-color-secondary: #a0a0a0;
}
```

## 贡献指南

1. 遵循现有的代码风格和规范
2. 为新组件添加完整的文档和测试
3. 确保组件的无障碍访问性
4. 提供TypeScript类型定义
5. 更新相关的README文档