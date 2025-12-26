# 设备组件 (Device Components)

这个目录包含与设备相关的可复用组件。

## 组件列表

### DeviceSelector.vue
设备选择器组件，提供设备搜索和选择功能。

**功能特性：**
- 远程搜索设备
- 支持设备类型过滤
- 支持状态过滤（如只显示在线设备）
- 显示设备状态指示器
- 支持禁用状态
- 缓存常用设备列表

**使用示例：**
```vue
<template>
  <DeviceSelector 
    v-model="selectedDeviceId"
    :device-type="'welding'"
    :online-only="true"
    @device-change="handleDeviceChange"
  />
</template>

<script setup>
import { DeviceSelector } from '@/components/device'

const selectedDeviceId = ref(null)

const handleDeviceChange = (device) => {
  console.log('选中的设备:', device)
}
</script>
```

**Props：**
- `modelValue`: 选中的设备ID
- `deviceType`: 设备类型过滤
- `disabled`: 是否禁用
- `placeholder`: 占位符文本
- `showStatus`: 是否显示设备状态
- `onlineOnly`: 是否只显示在线设备

**Events：**
- `update:modelValue`: 设备ID变化
- `device-change`: 设备对象变化

## 使用指南

1. **导入组件**
```javascript
import { DeviceSelector } from '@/components/device'
// 或者
import DeviceSelector from '@/components/device/DeviceSelector.vue'
```

2. **全局注册**
```javascript
import { installDeviceComponents } from '@/components/device'
installDeviceComponents(app)
```

## 扩展指南

如果需要添加新的设备相关组件：

1. 在此目录下创建新的 `.vue` 文件
2. 在 `index.js` 中添加导出
3. 更新此 README 文档
4. 考虑是否需要添加单元测试

## 依赖关系

- 依赖 `@/api/device-v2` 进行设备数据获取
- 依赖 `@/components/common/StatusIndicator` 显示设备状态
- 依赖 Naive UI 组件库