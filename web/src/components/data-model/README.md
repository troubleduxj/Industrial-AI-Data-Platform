# 数据模型管理 - 通用组件

本目录包含数据模型管理相关的可复用Vue组件。

## 组件列表

### 1. TransformRuleEditor（转换规则编辑器）

**状态**: ✅ 已集成到字段映射页面中

**功能**:
- 支持6种转换类型：expression、mapping、range_limit、unit、round、composite
- 动态表单根据转换类型显示
- 实时预览转换效果
- 语法验证

**使用示例**:
```vue
<template>
  <!-- 转换规则已集成在 mapping/index.vue 中 -->
  <n-form-item label="转换类型">
    <n-select v-model:value="transformType" :options="transformTypeOptions" />
  </n-form-item>
</template>
```

**位置**: `web/src/views/data-model/mapping/index.vue` (第 106-165 行)

### 2. FieldDetail（字段详情预览）

**状态**: 💡 可选增强组件

**功能**:
- 显示字段基本信息（名称、代码、类型）
- 显示字段单位和数据范围
- 显示报警阈值配置
- 显示显示配置

**建议实现**:
```vue
<!-- web/src/components/data-model/FieldDetail.vue -->
<template>
  <n-descriptions :column="2" bordered size="small">
    <n-descriptions-item label="字段名称">
      {{ field.field_name }}
    </n-descriptions-item>
    <n-descriptions-item label="字段代码">
      {{ field.field_code }}
    </n-descriptions-item>
    <!-- 更多字段... -->
  </n-descriptions>
</template>
```

### 3. SQLHighlight（SQL语法高亮）

**状态**: ✅ 已使用 Naive UI 的 n-code 组件

**功能**:
- SQL语法高亮显示
- 支持复制
- 自动换行

**使用示例**:
```vue
<template>
  <!-- 在 preview/index.vue 中已使用 -->
  <n-code 
    :code="generatedSQL" 
    language="sql"
    word-wrap
  />
</template>
```

**位置**: `web/src/views/data-model/preview/index.vue` (第 86-91 行)

## 组件开发指南

### 创建新组件

1. 在此目录下创建组件文件
2. 使用 Vue 3 Composition API
3. 使用 Naive UI 组件库
4. 添加 TypeScript 类型支持（可选）
5. 编写组件文档

### 示例组件模板

```vue
<template>
  <div class="component-name">
    <!-- 组件内容 -->
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// 组件逻辑
</script>

<style scoped>
.component-name {
  /* 样式 */
}
</style>
```

## 当前状态

所有核心功能已集成到三个主要页面中：

1. ✅ **config/index.vue** - 模型配置管理
2. ✅ **mapping/index.vue** - 字段映射管理（包含转换规则编辑器）
3. ✅ **preview/index.vue** - 数据预览与测试（包含SQL高亮）

如需将这些功能抽取为独立组件，可以在此目录下创建并导出。

