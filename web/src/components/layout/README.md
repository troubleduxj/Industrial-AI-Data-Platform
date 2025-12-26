# 布局组件库

本目录包含响应式布局相关的组件，提供灵活的栅格系统、容器管理和断点检测功能。

## 组件列表

### ResponsiveGrid
响应式栅格容器组件，提供灵活的栅格布局系统。

**功能特性:**
- 响应式列数配置
- 自定义间距设置
- 自动填充模式
- 密集布局支持
- 对齐方式配置

**使用示例:**
```vue
<template>
  <ResponsiveGrid 
    :cols="{ xs: 1, sm: 2, md: 3, lg: 4 }" 
    :gap="16"
    justify="center"
  >
    <ResponsiveGridItem v-for="item in items" :key="item.id">
      <DeviceCard :device="item" />
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

**自动填充模式:**
```vue
<template>
  <ResponsiveGrid 
    :auto-fit="true"
    min-col-width="250px"
    :gap="20"
  >
    <ResponsiveGridItem v-for="item in items" :key="item.id">
      <Card>{{ item.content }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

### ResponsiveGridItem
响应式栅格项组件，支持跨列、跨行和响应式配置。

**功能特性:**
- 响应式跨列配置
- 跨行支持
- 偏移设置
- 精确位置控制
- 排序功能

**使用示例:**
```vue
<template>
  <ResponsiveGrid :cols="{ xs: 1, md: 3 }">
    <!-- 普通项目 -->
    <ResponsiveGridItem>
      <Card>内容1</Card>
    </ResponsiveGridItem>
    
    <!-- 跨列项目 -->
    <ResponsiveGridItem :span="{ xs: 1, md: 2 }">
      <Card>跨两列的内容</Card>
    </ResponsiveGridItem>
    
    <!-- 带偏移的项目 -->
    <ResponsiveGridItem :offset="{ md: 1 }">
      <Card>偏移一列</Card>
    </ResponsiveGridItem>
    
    <!-- 精确位置控制 -->
    <ResponsiveGridItem :col-start="2" :col-end="4">
      <Card>占据第2-3列</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

### ResponsiveContainer
响应式容器组件，提供响应式的容器宽度和内边距管理。

**功能特性:**
- 多种容器尺寸
- 流式布局支持
- 响应式内边距
- 居中对齐
- 自定义最大/最小宽度

**使用示例:**
```vue
<template>
  <!-- 标准容器 -->
  <ResponsiveContainer size="lg">
    <h1>页面标题</h1>
    <p>页面内容</p>
  </ResponsiveContainer>
  
  <!-- 流式容器 -->
  <ResponsiveContainer :fluid="true">
    <div>全宽内容</div>
  </ResponsiveContainer>
  
  <!-- 自定义内边距 -->
  <ResponsiveContainer 
    :padding="{ xs: 12, md: 24, lg: 32 }"
    max-width="800px"
  >
    <Article />
  </ResponsiveContainer>
</template>
```

### BreakpointProvider
断点提供者组件，监听屏幕尺寸变化，提供当前断点信息。

**功能特性:**
- 实时断点检测
- 设备类型判断
- 屏幕尺寸监听
- 自定义断点配置
- 防抖处理

**使用示例:**
```vue
<template>
  <BreakpointProvider>
    <template #default="{ breakpoint, isMobile, isDesktop, screenWidth }">
      <div v-if="isMobile" class="mobile-layout">
        <MobileNavigation />
        <MobileContent />
      </div>
      
      <div v-else-if="isDesktop" class="desktop-layout">
        <Sidebar />
        <MainContent />
      </div>
      
      <div class="debug-info">
        当前断点: {{ breakpoint }} | 屏幕宽度: {{ screenWidth }}px
      </div>
    </template>
  </BreakpointProvider>
</template>
```

## 组合式函数

### useResponsive
响应式断点检测组合式函数。

**使用示例:**
```vue
<script setup>
import { useResponsive } from '@/composables/useResponsive'

const {
  currentBreakpoint,
  isMobile,
  isDesktop,
  screenWidth,
  isLgAndUp
} = useResponsive()

// 监听断点变化
watch(currentBreakpoint, (newBreakpoint) => {
  console.log('断点变化:', newBreakpoint)
})
</script>

<template>
  <div>
    <div v-if="isMobile">移动端布局</div>
    <div v-else-if="isDesktop">桌面端布局</div>
    
    <div v-show="isLgAndUp">大屏幕专用内容</div>
  </div>
</template>
```

### useResponsiveValue
响应式值选择器。

**使用示例:**
```vue
<script setup>
import { useResponsiveValue } from '@/composables/useResponsive'

const columns = useResponsiveValue({
  xs: 1,
  sm: 2,
  md: 3,
  lg: 4,
  xl: 6
}, 1)

const cardSize = useResponsiveValue({
  xs: 'small',
  md: 'medium',
  lg: 'large'
}, 'medium')
</script>

<template>
  <ResponsiveGrid :cols="columns">
    <ResponsiveGridItem v-for="item in items" :key="item.id">
      <Card :size="cardSize">{{ item.content }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

### useMediaQuery
媒体查询匹配器。

**使用示例:**
```vue
<script setup>
import { useMediaQuery } from '@/composables/useResponsive'

const { matches: isLargeScreen } = useMediaQuery('(min-width: 1024px)')
const { matches: isDarkMode } = useMediaQuery('(prefers-color-scheme: dark)')
const { matches: isHighDensity } = useMediaQuery('(min-resolution: 2dppx)')
</script>

<template>
  <div>
    <div v-if="isLargeScreen">大屏幕内容</div>
    <div v-if="isDarkMode">暗色主题激活</div>
    <div v-if="isHighDensity">高分辨率屏幕</div>
  </div>
</template>
```

## 断点配置

### 默认断点
```javascript
const breakpoints = {
  xs: 0,      // 超小屏幕 <576px
  sm: 576,    // 小屏幕 ≥576px
  md: 768,    // 中等屏幕 ≥768px
  lg: 992,    // 大屏幕 ≥992px
  xl: 1200,   // 超大屏幕 ≥1200px
  xxl: 1600   // 超超大屏幕 ≥1600px
}
```

### 自定义断点
```vue
<script setup>
import { useResponsive } from '@/composables/useResponsive'

// 自定义断点配置
const customBreakpoints = {
  mobile: 0,
  tablet: 640,
  laptop: 1024,
  desktop: 1440
}

const { currentBreakpoint } = useResponsive(customBreakpoints)
</script>
```

## 布局模式

### 栅格布局
```vue
<template>
  <!-- 基础栅格 -->
  <ResponsiveGrid :cols="4" :gap="16">
    <ResponsiveGridItem v-for="i in 8" :key="i">
      <Card>项目 {{ i }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
  
  <!-- 响应式栅格 -->
  <ResponsiveGrid :cols="{ xs: 1, sm: 2, md: 3, lg: 4 }">
    <ResponsiveGridItem v-for="item in items" :key="item.id">
      <Card>{{ item.title }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
  
  <!-- 不规则布局 -->
  <ResponsiveGrid :cols="{ xs: 1, md: 4 }">
    <ResponsiveGridItem :span="{ xs: 1, md: 2 }">
      <Card>主要内容</Card>
    </ResponsiveGridItem>
    <ResponsiveGridItem>
      <Card>侧边栏1</Card>
    </ResponsiveGridItem>
    <ResponsiveGridItem>
      <Card>侧边栏2</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

### 自适应布局
```vue
<template>
  <!-- 自动填充 -->
  <ResponsiveGrid 
    :auto-fit="true"
    min-col-width="200px"
    max-col-width="300px"
  >
    <ResponsiveGridItem v-for="item in items" :key="item.id">
      <Card>{{ item.content }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
  
  <!-- 密集布局 -->
  <ResponsiveGrid 
    :cols="{ xs: 2, md: 4, lg: 6 }"
    :dense="true"
  >
    <ResponsiveGridItem 
      v-for="item in items" 
      :key="item.id"
      :span="item.featured ? 2 : 1"
      :row-span="item.tall ? 2 : 1"
    >
      <Card :class="{ featured: item.featured }">
        {{ item.content }}
      </Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

## 样式定制

### CSS变量
```css
:root {
  /* 断点变量 */
  --breakpoint-xs: 0px;
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
  --breakpoint-xxl: 1600px;
  
  /* 容器最大宽度 */
  --container-sm: 576px;
  --container-md: 768px;
  --container-lg: 992px;
  --container-xl: 1200px;
  --container-xxl: 1600px;
  
  /* 间距变量 */
  --spacing-xs: 8px;
  --spacing-sm: 12px;
  --spacing-md: 16px;
  --spacing-lg: 20px;
  --spacing-xl: 24px;
  --spacing-xxl: 32px;
}
```

### 主题定制
```css
/* 栅格主题 */
.responsive-grid {
  --grid-gap: 16px;
  --grid-padding: 0;
}

/* 容器主题 */
.responsive-container {
  --container-padding-xs: 16px;
  --container-padding-sm: 20px;
  --container-padding-md: 24px;
  --container-padding-lg: 32px;
  --container-padding-xl: 40px;
  --container-padding-xxl: 48px;
}

/* 暗色主题 */
.dark {
  --grid-border-color: #333;
  --container-bg-color: #1a1a1a;
}
```

## 性能优化

### 懒加载
```javascript
// 按需加载布局组件
const ResponsiveGrid = defineAsyncComponent(() => 
  import('@/components/layout/ResponsiveGrid.vue')
)
```

### 防抖优化
```javascript
// 自定义防抖延迟
const { currentBreakpoint } = useResponsive({}, 200) // 200ms防抖
```

### 内存优化
```javascript
// 使用全局单例模式减少内存占用
// useResponsive 内部使用单例模式管理全局屏幕尺寸监听
```

## 无障碍访问

### 语义化标签
```vue
<template>
  <ResponsiveContainer tag="main" role="main">
    <ResponsiveGrid tag="section" aria-label="产品列表">
      <ResponsiveGridItem 
        v-for="product in products" 
        :key="product.id"
        tag="article"
        role="article"
      >
        <ProductCard :product="product" />
      </ResponsiveGridItem>
    </ResponsiveGrid>
  </ResponsiveContainer>
</template>
```

### 键盘导航
```vue
<template>
  <ResponsiveGrid>
    <ResponsiveGridItem 
      v-for="(item, index) in items" 
      :key="item.id"
      :tabindex="0"
      @keydown.enter="handleItemSelect(item)"
      @keydown.space="handleItemSelect(item)"
    >
      <Card>{{ item.content }}</Card>
    </ResponsiveGridItem>
  </ResponsiveGrid>
</template>
```

## 测试指南

### 单元测试
```javascript
import { mount } from '@vue/test-utils'
import ResponsiveGrid from '../ResponsiveGrid.vue'

describe('ResponsiveGrid', () => {
  it('renders with correct columns', () => {
    const wrapper = mount(ResponsiveGrid, {
      props: { cols: 3 }
    })
    
    expect(wrapper.element.style.gridTemplateColumns).toBe('repeat(3, 1fr)')
  })
  
  it('applies responsive columns', async () => {
    // 模拟屏幕尺寸变化
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768
    })
    
    const wrapper = mount(ResponsiveGrid, {
      props: { cols: { xs: 1, md: 3 } }
    })
    
    // 触发resize事件
    window.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()
    
    // 验证响应式行为
    expect(wrapper.vm.currentBreakpoint).toBe('md')
  })
})
```

### 集成测试
```javascript
import { mount } from '@vue/test-utils'
import { useResponsive } from '@/composables/useResponsive'

describe('useResponsive', () => {
  it('detects breakpoint correctly', () => {
    // 模拟不同屏幕尺寸
    const testCases = [
      { width: 320, expected: 'xs' },
      { width: 768, expected: 'md' },
      { width: 1200, expected: 'xl' }
    ]
    
    testCases.forEach(({ width, expected }) => {
      Object.defineProperty(window, 'innerWidth', { value: width })
      
      const { currentBreakpoint } = useResponsive()
      expect(currentBreakpoint.value).toBe(expected)
    })
  })
})
```

## 最佳实践

1. **移动端优先**: 始终从最小屏幕开始设计，逐步增强
2. **合理断点**: 根据内容而非设备选择断点
3. **性能考虑**: 避免过度嵌套和复杂的响应式逻辑
4. **可访问性**: 确保在所有设备上都能正常使用
5. **测试覆盖**: 在不同屏幕尺寸下测试布局效果

## 常见问题

### Q: 如何处理复杂的响应式布局？
A: 使用 ResponsiveGrid 的嵌套和 ResponsiveGridItem 的跨列功能，结合 useResponsive 进行条件渲染。

### Q: 如何优化大量栅格项的性能？
A: 使用虚拟滚动、懒加载和 v-memo 指令优化渲染性能。

### Q: 如何实现自定义断点？
A: 通过 useResponsive 的第一个参数传入自定义断点配置。

### Q: 如何处理容器查询？
A: 使用 useContainerQuery 组合式函数实现基于容器尺寸的响应式布局。