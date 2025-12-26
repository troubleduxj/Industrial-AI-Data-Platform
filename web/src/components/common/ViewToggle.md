# ViewToggle 视图切换组件

统一的视图模式切换组件，用于在不同的数据展示方式之间进行切换。

## 设计原则

### 1. 统一性

- 所有页面使用相同的视图切换样式和交互
- 统一的图标和文字标识
- 一致的位置布局和尺寸规范

### 2. 可访问性

- 支持键盘导航
- 明确的视觉状态反馈
- 适当的颜色对比度

### 3. 响应式设计

- 移动端自动适配
- 支持紧凑模式
- 灵活的布局选项

## 组件属性

| 属性名     | 类型    | 默认值  | 说明                              |
| ---------- | ------- | ------- | --------------------------------- |
| modelValue | String  | -       | 当前选中的视图模式（必需）        |
| options    | Array   | -       | 视图选项配置（必需）              |
| size       | String  | 'small' | 组件尺寸：tiny/small/medium/large |
| showLabel  | Boolean | true    | 是否显示标签文字                  |
| iconSize   | Number  | 16      | 图标尺寸                          |
| disabled   | Boolean | false   | 是否禁用                          |
| align      | String  | 'right' | 对齐方式：left/center/right       |
| compact    | Boolean | false   | 是否紧凑模式（仅显示图标）        |

## 事件

| 事件名            | 说明               | 参数            |
| ----------------- | ------------------ | --------------- |
| update:modelValue | 视图模式改变时触发 | (value: string) |
| change            | 视图模式改变时触发 | (value: string) |

## 选项配置格式

```javascript
const options = [
  {
    value: 'table', // 视图模式值
    label: '表格视图', // 显示标签
    icon: 'material-symbols:table-chart', // 图标
  },
  {
    value: 'card',
    label: '卡片视图',
    icon: 'material-symbols:grid-view',
  },
]
```

## 使用示例

### 基础用法

```vue
<template>
  <div>
    <!-- 视图切换组件 -->
    <ViewToggle v-model="viewMode" :options="viewOptions" @change="handleViewChange" />

    <!-- 根据视图模式显示不同内容 -->
    <div v-if="viewMode === 'table'">
      <!-- 表格视图 -->
    </div>
    <div v-else-if="viewMode === 'card'">
      <!-- 卡片视图 -->
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import { TABLE_CARD_OPTIONS } from '@/components/common/view-toggle-options.js'

const viewMode = ref('table')
const viewOptions = TABLE_CARD_OPTIONS

function handleViewChange(mode) {
  console.log('视图模式切换为:', mode)
  // 可以在这里处理视图切换的副作用
}
</script>
```

### 实际应用示例

#### 1. 设备监控页面

```vue
<template>
  <CommonPage show-footer>
    <template #action>
      <div class="flex items-center justify-between w-full">
        <!-- 左侧操作按钮 -->
        <div class="flex items-center gap-10">
          <NButton type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建设备
          </NButton>
        </div>

        <!-- 右侧视图切换 -->
        <ViewToggle
          v-model="viewMode"
          :options="viewOptions"
          size="small"
          :show-label="false"
          :icon-size="16"
          align="right"
        />
      </div>
    </template>

    <!-- 卡片视图 -->
    <div
      v-if="viewMode === 'card'"
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <!-- 设备卡片 -->
    </div>

    <!-- 表格视图 -->
    <CrudTable v-else-if="viewMode === 'table'" />
  </CommonPage>
</template>

<script setup>
import { ref } from 'vue'
import ViewToggle from '@/components/common/ViewToggle.vue'

const viewMode = ref('card')
const viewOptions = [
  {
    value: 'card',
    label: '卡片',
    icon: 'material-symbols:grid-view',
  },
  {
    value: 'table',
    label: '表格',
    icon: 'material-symbols:table-chart',
  },
]
</script>
```

#### 2. 统计页面（图表/表格切换）

```vue
<template>
  <CommonPage show-footer>
    <template #action>
      <div class="flex items-center justify-between w-full">
        <!-- 查询条件 -->
        <div class="flex items-center gap-10">
          <!-- 查询表单 -->
        </div>

        <!-- 视图切换 -->
        <ViewToggle
          v-model="viewMode"
          :options="viewOptions"
          size="small"
          :show-label="false"
          :icon-size="16"
          align="right"
        />
      </div>
    </template>

    <!-- 图表视图 -->
    <div v-if="viewMode === 'chart'" class="chart-container">
      <div ref="chartRef" class="w-full h-400px"></div>
    </div>

    <!-- 表格视图 -->
    <CrudTable v-else-if="viewMode === 'table'" />
  </CommonPage>
</template>

<script setup>
import { ref, watch } from 'vue'
import ViewToggle from '@/components/common/ViewToggle.vue'

const viewMode = ref('chart')
const chartRef = ref(null)

const viewOptions = [
  {
    value: 'chart',
    label: '图表',
    icon: 'material-symbols:bar-chart',
  },
  {
    value: 'table',
    label: '表格',
    icon: 'material-symbols:table-chart',
  },
]

// 监听视图切换，初始化图表
watch(viewMode, (newMode) => {
  if (newMode === 'chart') {
    nextTick(() => {
      initChart()
    })
  }
})
</script>
```

### 使用预定义选项

```vue
<script setup>
import {
  TABLE_CARD_OPTIONS,
  CHART_TABLE_OPTIONS,
  DEVICE_VIEW_OPTIONS,
  getViewOptionsByPageType,
} from '@/components/common/view-toggle-options.js'

// 直接使用预定义选项
const deviceOptions = DEVICE_VIEW_OPTIONS

// 根据页面类型获取选项
const pageOptions = getViewOptionsByPageType('statistics')
</script>
```

### 自定义选项

```vue
<script setup>
const customOptions = [
  {
    value: 'timeline',
    label: '时间线视图',
    icon: 'material-symbols:timeline',
  },
  {
    value: 'kanban',
    label: '看板视图',
    icon: 'material-symbols:view-kanban',
  },
]
</script>
```

### 紧凑模式

```vue
<template>
  <!-- 仅显示图标，适用于空间受限的场景 -->
  <ViewToggle v-model="viewMode" :options="options" compact size="tiny" />
</template>
```

### 不同对齐方式

```vue
<template>
  <!-- 左对齐 -->
  <ViewToggle v-model="viewMode" :options="options" align="left" />

  <!-- 居中对齐 -->
  <ViewToggle v-model="viewMode" :options="options" align="center" />

  <!-- 右对齐（默认） -->
  <ViewToggle v-model="viewMode" :options="options" align="right" />
</template>
```

## 布局建议

### 1. 位置规范

**推荐位置（优先级从高到低）：**

1. **页面操作区域右侧**（最推荐）

   ```vue
   <template #action>
     <div class="flex items-center gap-10">
       <!-- 其他操作按钮 -->
       <ViewToggle v-model="viewMode" :options="options" />
     </div>
   </template>
   ```

2. **内容区域右上角**

   ```vue
   <div class="mb-4 flex justify-end">
     <ViewToggle v-model="viewMode" :options="options" />
   </div>
   ```

3. **工具栏中间位置**
   ```vue
   <div class="toolbar flex items-center justify-between">
     <div><!-- 左侧工具 --></div>
     <ViewToggle v-model="viewMode" :options="options" />
     <div><!-- 右侧工具 --></div>
   </div>
   ```

### 2. 间距规范

- 与其他元素的最小间距：`8px`
- 推荐间距：`12px` - `16px`
- 在操作区域中的间距：`10px`

### 3. 尺寸选择

| 场景           | 推荐尺寸       | 说明             |
| -------------- | -------------- | ---------------- |
| 页面主要操作区 | small          | 标准尺寸，最常用 |
| 工具栏         | tiny           | 紧凑场景         |
| 独立展示区域   | medium         | 需要突出显示时   |
| 移动端         | tiny + compact | 节省空间         |

## 最佳实践

### 1. 状态管理

```vue
<script setup>
import { ref, watch } from 'vue'

const viewMode = ref('table')

// 监听视图模式变化，执行相关逻辑
watch(viewMode, (newMode) => {
  // 保存用户偏好
  localStorage.setItem('preferredViewMode', newMode)

  // 触发数据重新加载（如果需要）
  if (newMode === 'chart') {
    loadChartData()
  }
})

// 初始化时恢复用户偏好
const savedMode = localStorage.getItem('preferredViewMode')
if (savedMode) {
  viewMode.value = savedMode
}
</script>
```

### 2. 响应式处理

```vue
<script setup>
import { ref, computed } from 'vue'
import { useBreakpoints } from '@/composables/useBreakpoints'

const { isMobile } = useBreakpoints()

// 移动端自动使用紧凑模式
const isCompact = computed(() => isMobile.value)
const toggleSize = computed(() => (isMobile.value ? 'tiny' : 'small'))
</script>

<template>
  <ViewToggle v-model="viewMode" :options="options" :compact="isCompact" :size="toggleSize" />
</template>
```

### 3. 无障碍访问

```vue
<template>
  <div role="group" aria-label="视图切换">
    <ViewToggle v-model="viewMode" :options="options" @change="announceViewChange" />
  </div>
</template>

<script setup>
function announceViewChange(mode) {
  const option = options.find((opt) => opt.value === mode)
  // 使用屏幕阅读器宣布变化
  const announcement = `已切换到${option.label}`
  // 实现屏幕阅读器通知逻辑
}
</script>
```

### 4. 性能优化

```vue
<script setup>
import { ref, shallowRef } from 'vue'

// 对于大量数据的视图切换，使用 shallowRef 优化性能
const tableData = shallowRef([])
const chartData = shallowRef([])

function handleViewChange(mode) {
  // 延迟加载数据，避免不必要的计算
  nextTick(() => {
    if (mode === 'table' && !tableData.value.length) {
      loadTableData()
    } else if (mode === 'chart' && !chartData.value.length) {
      loadChartData()
    }
  })
}
</script>
```

## 迁移指南

### 从现有实现迁移

#### 1. 设备监控页面迁移示例

**原有代码：**

```vue
<template>
  <CommonPage show-footer>
    <template #action>
      <div class="flex items-center gap-10">
        <NButton type="primary" @click="handleAdd">
          <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建设备
        </NButton>
      </div>
    </template>

    <!-- 视图切换按钮 -->
    <div class="mb-4 flex justify-end">
      <NButton
        :type="viewMode === 'table' ? 'primary' : 'default'"
        @click="toggleViewMode('table')"
        class="mr-2"
      >
        <TheIcon icon="material-symbols:table-chart" :size="16" class="mr-1" />
        表格视图
      </NButton>
      <NButton :type="viewMode === 'card' ? 'primary' : 'default'" @click="toggleViewMode('card')">
        <TheIcon icon="material-symbols:grid-view" :size="16" class="mr-1" />
        卡片视图
      </NButton>
    </div>
  </CommonPage>
</template>

<script setup>
const viewMode = ref('card')

const toggleViewMode = (mode) => {
  viewMode.value = mode
}
</script>

<style scoped>
.view-toggle-group {
  display: flex;
  gap: 8px;
}
</style>
```

**新的实现方式：**

```vue
<template>
  <CommonPage show-footer>
    <template #action>
      <div class="flex items-center justify-between w-full">
        <!-- 左侧操作按钮 -->
        <div class="flex items-center gap-10">
          <NButton type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建设备
          </NButton>
        </div>

        <!-- 右侧视图切换 -->
        <ViewToggle
          v-model="viewMode"
          :options="viewOptions"
          size="small"
          :show-label="false"
          :icon-size="16"
          align="right"
        />
      </div>
    </template>
  </CommonPage>
</template>

<script setup>
import ViewToggle from '@/components/common/ViewToggle.vue'

const viewMode = ref('card')

// 视图切换选项
const viewOptions = [
  {
    value: 'card',
    label: '卡片',
    icon: 'material-symbols:grid-view',
  },
  {
    value: 'table',
    label: '表格',
    icon: 'material-symbols:table-chart',
  },
]

// 不再需要 toggleViewMode 函数，由 v-model 自动处理
</script>

<!-- 不再需要自定义样式 -->
```

#### 2. 统计页面迁移示例

**原有代码：**

```vue
<template>
  <div class="mb-4 flex justify-end">
    <div class="view-toggle-group">
      <NButton
        :type="viewMode === 'chart' ? 'primary' : 'default'"
        @click="toggleView('chart')"
        size="small"
      >
        <TheIcon icon="material-symbols:bar-chart" :size="16" class="mr-1" />
        图表视图
      </NButton>
      <NButton
        :type="viewMode === 'table' ? 'primary' : 'default'"
        @click="toggleView('table')"
        size="small"
      >
        <TheIcon icon="material-symbols:table-chart" :size="16" class="mr-1" />
        表格视图
      </NButton>
    </div>
  </div>
</template>

<script setup>
const toggleView = (mode) => {
  viewMode.value = mode
  if (mode === 'chart') {
    nextTick(() => {
      initChart()
    })
  }
}
</script>
```

**新的实现方式：**

```vue
<template>
  <template #action>
    <div class="flex items-center justify-between w-full">
      <!-- 查询条件等 -->
      <div class="flex items-center gap-10">
        <!-- 其他操作 -->
      </div>

      <!-- 视图切换 -->
      <ViewToggle
        v-model="viewMode"
        :options="viewOptions"
        size="small"
        :show-label="false"
        :icon-size="16"
        align="right"
      />
    </div>
  </template>
</template>

<script setup>
import { watch } from 'vue'
import ViewToggle from '@/components/common/ViewToggle.vue'

const viewOptions = [
  {
    value: 'chart',
    label: '图表',
    icon: 'material-symbols:bar-chart',
  },
  {
    value: 'table',
    label: '表格',
    icon: 'material-symbols:table-chart',
  },
]

// 使用 watch 监听视图切换
watch(viewMode, (newMode) => {
  if (newMode === 'chart') {
    nextTick(() => {
      initChart()
    })
  }
})
</script>
```

### 样式迁移

移除原有的 CSS 样式定义：

```css
/* 删除这些样式 */
.view-toggle-group {
  /* ... */
}
.view-toggle-group .n-button {
  /* ... */
}
/* ... */
```

## 扩展开发

### 添加新的预定义选项

在 `view-toggle-options.js` 中添加：

```javascript
export const NEW_VIEW_OPTIONS = [
  {
    value: 'new-view',
    label: '新视图',
    icon: 'material-symbols:new-icon',
  },
]
```

### 自定义主题

```css
/* 在全局样式中覆盖 CSS 变量 */
:root {
  --view-toggle-border-color: #custom-color;
  --view-toggle-bg-color: #custom-bg;
  --view-toggle-primary-color: #custom-primary;
}
```

## 常见问题

### Q: 如何在移动端优化显示？

A: 使用 `compact` 属性和较小的 `size`，或者根据屏幕尺寸动态调整。

### Q: 可以自定义图标吗？

A: 可以，在 options 中指定任何支持的图标名称。

### Q: 如何处理视图切换时的数据加载？

A: 在 `change` 事件中处理，建议使用懒加载策略。

### Q: 支持键盘导航吗？

A: 是的，组件基于 NButton 实现，天然支持键盘导航。

## 项目应用情况

### 已应用页面

当前项目中已成功应用 ViewToggle 组件的页面：

1. **设备监控页面** (`/views/device/monitor/index.vue`)

   - 视图模式：卡片视图 ↔ 表格视图
   - 位置：页面操作区域右侧
   - 配置：纯图标模式，小尺寸

2. **设备基础信息页面** (`/views/device/baseinfo/index.vue`)

   - 视图模式：表格视图 ↔ 卡片视图
   - 位置：页面操作区域右侧
   - 配置：纯图标模式，小尺寸

3. **焊接时长统计页面** (`/views/statistics/weld_time/index.vue`)

   - 视图模式：图表视图 ↔ 表格视图
   - 位置：页面操作区域右侧
   - 配置：纯图标模式，小尺寸

4. **在线率统计页面** (`/views/statistics/online_rate/index.vue`)
   - 视图模式：图表视图 ↔ 表格视图
   - 位置：页面操作区域右侧
   - 配置：纯图标模式，小尺寸

### 统一效果

通过使用 ViewToggle 组件，项目实现了：

- ✅ **视觉一致性**：所有页面的视图切换按钮样式统一
- ✅ **交互一致性**：统一的切换方式和响应效果
- ✅ **代码复用**：减少重复代码，提高可维护性
- ✅ **用户体验**：一致的操作习惯，降低学习成本
- ✅ **响应式设计**：自适应不同屏幕尺寸

### 迁移收益

从原有的自定义按钮组迁移到 ViewToggle 组件后：

1. **代码减少**：每个页面减少约 20-30 行模板代码
2. **样式统一**：移除了各页面的自定义样式定义
3. **功能增强**：自动支持键盘导航、无障碍访问等特性
4. **维护简化**：样式和行为的修改只需在组件中进行
5. **扩展性强**：新增页面可直接使用，无需重复开发

### 最佳实践总结

基于项目实际应用，推荐的最佳实践：

1. **位置布局**：优先放置在页面操作区域的右侧
2. **配置参数**：使用 `size="small"` 和 `:show-label="false"`
3. **图标尺寸**：设置 `:icon-size="16"` 保持视觉平衡
4. **对齐方式**：使用 `align="right"` 与操作区域对齐
5. **响应式**：在移动端可考虑使用更紧凑的配置
