# 卡片组件库

本目录包含了项目中统一的卡片组件，用于保持界面风格的一致性。

## 组件列表

### BaseCard - 基础卡片组件

通用的基础卡片组件，提供统一的样式和交互行为。

#### 属性

| 属性名    | 类型          | 默认值    | 说明                                                 |
| --------- | ------------- | --------- | ---------------------------------------------------- |
| title     | String        | ''        | 卡片标题                                             |
| icon      | String        | ''        | 标题图标                                             |
| iconSize  | Number        | 16        | 图标大小                                             |
| type      | String        | 'default' | 卡片类型：default/primary/success/warning/error/info |
| size      | String        | 'medium'  | 卡片尺寸：small/medium/large                         |
| hoverable | Boolean       | false     | 是否可悬停                                           |
| clickable | Boolean       | false     | 是否可点击                                           |
| bordered  | Boolean       | true      | 是否显示边框                                         |
| shadow    | String        | 'hover'   | 阴影显示：never/hover/always                         |
| rounded   | String/Number | 8         | 圆角大小                                             |
| padding   | String        | 'default' | 内边距：none/small/default/large                     |

#### 插槽

| 插槽名  | 说明           |
| ------- | -------------- |
| default | 卡片主要内容   |
| header  | 自定义头部内容 |
| footer  | 自定义底部内容 |
| action  | 操作区域       |
| extra   | 头部额外内容   |

#### 事件

| 事件名 | 说明                                   | 参数  |
| ------ | -------------------------------------- | ----- |
| click  | 点击事件（需要设置 clickable 为 true） | event |

#### 使用示例

```vue
<template>
  <BaseCard
    title="基础卡片"
    icon="mdi:card-outline"
    type="primary"
    hoverable
    clickable
    @click="handleCardClick"
  >
    <p>这是卡片内容</p>

    <template #extra>
      <NButton size="small">操作</NButton>
    </template>
  </BaseCard>
</template>
```

### StatCard - 统计卡片组件

专门用于显示统计数据的卡片组件。

#### 属性

| 属性名     | 类型          | 默认值    | 说明                 |
| ---------- | ------------- | --------- | -------------------- |
| title      | String        | ''        | 统计项标题           |
| value      | String/Number | ''        | 统计数值             |
| unit       | String        | ''        | 数值单位             |
| icon       | String        | ''        | 图标                 |
| type       | String        | 'default' | 卡片类型             |
| size       | String        | 'medium'  | 卡片尺寸             |
| trend      | String        | ''        | 趋势：up/down/stable |
| trendValue | String/Number | ''        | 趋势数值             |
| loading    | Boolean       | false     | 加载状态             |
| clickable  | Boolean       | false     | 是否可点击           |

#### 使用示例

```vue
<template>
  <StatCard
    title="在线设备"
    :value="1234"
    unit="台"
    icon="mdi:devices"
    type="success"
    trend="up"
    trend-value="+5.2%"
  />
</template>
```

### DeviceCard - 设备卡片组件

专门用于显示设备信息的卡片组件。

#### 属性

| 属性名      | 类型    | 默认值   | 说明             |
| ----------- | ------- | -------- | ---------------- |
| device      | Object  | {}       | 设备信息对象     |
| showActions | Boolean | true     | 是否显示操作按钮 |
| size        | String  | 'medium' | 卡片尺寸         |
| clickable   | Boolean | false    | 是否可点击       |

#### 设备信息对象结构

```javascript
{
  id: '设备ID',
  name: '设备名称',
  type: '设备类型',
  status: '设备状态', // online/offline/error/maintenance
  location: '设备位置',
  lastUpdate: '最后更新时间',
  data: {
    // 监控数据
    temperature: 25.5,
    humidity: 60,
    // ...
  }
}
```

#### 使用示例

```vue
<template>
  <DeviceCard
    :device="deviceInfo"
    :show-actions="true"
    clickable
    @click="handleDeviceClick"
    @edit="handleEdit"
    @delete="handleDelete"
  />
</template>
```

## 导入方式

### 单独导入

```javascript
import BaseCard from '@/components/card/BaseCard.vue'
import StatCard from '@/components/card/StatCard.vue'
import DeviceCard from '@/components/card/DeviceCard.vue'
```

### 批量导入

```javascript
import { BaseCard, StatCard, DeviceCard } from '@/components/card'
```

## 样式定制

所有卡片组件都支持通过 CSS 变量进行样式定制：

```css
:root {
  --card-border-radius: 8px;
  --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  --card-hover-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  --card-primary-color: #18a058;
  --card-success-color: #18a058;
  --card-warning-color: #f0a020;
  --card-error-color: #d03050;
  --card-info-color: #2080f0;
}
```

## 最佳实践

1. **统一使用**：新页面应优先使用这些统一的卡片组件，而不是自定义样式
2. **合理选择**：根据使用场景选择合适的卡片组件类型
3. **保持一致**：同一页面中的卡片应使用相同的尺寸和样式
4. **响应式设计**：在移动端适当调整卡片尺寸和内边距
5. **无障碍访问**：为可点击的卡片添加适当的 ARIA 标签

## 扩展指南

如需添加新的卡片类型：

1. 继承 `BaseCard` 组件
2. 添加特定的属性和样式
3. 更新 `index.js` 导出文件
4. 更新本文档说明

示例：

```vue
<template>
  <BaseCard v-bind="$attrs" class="custom-card">
    <!-- 自定义内容 -->
    <slot></slot>
  </BaseCard>
</template>

<script setup>
import BaseCard from './BaseCard.vue'

// 自定义属性和逻辑
</script>

<style scoped>
.custom-card {
  /* 自定义样式 */
}
</style>
```
