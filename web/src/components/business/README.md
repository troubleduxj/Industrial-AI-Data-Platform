# 业务组件库

本目录包含项目中特定业务领域的可复用组件，这些组件包含业务逻辑和数据处理，专门为特定的业务场景设计。

## 组件分类

### 设备相关组件 (Device Components)

#### DeviceStatusCard
设备状态卡片组件，用于显示设备的状态、监控数据和基本操作。

**功能特性:**
- 设备状态展示（运行中、离线、维护中、故障）
- 监控指标展示（电流、电压、温度等）
- 设备类型标识
- 位置信息显示
- 最后更新时间
- 操作按钮（查看详情、控制等）
- 自定义指标支持
- 响应式设计

**使用示例:**
```vue
<template>
  <DeviceStatusCard
    :device="deviceData"
    :show-metrics="true"
    :show-actions="true"
    :clickable="true"
    @click="handleDeviceClick"
    @view-details="handleViewDetails"
    @toggle-control="handleToggleControl"
  >
    <template #content="{ device }">
      <!-- 自定义内容 -->
    </template>
    
    <template #actions="{ device }">
      <!-- 自定义操作按钮 -->
    </template>
  </DeviceStatusCard>
</template>

<script setup>
const deviceData = {
  id: 'DEV001',
  name: '焊接设备A',
  status: 'active',
  device_type: 'welding',
  location: '车间A-01',
  preset_current: 274.0,
  preset_voltage: 26.8,
  welding_current: 82.0,
  welding_voltage: 21.2,
  lastUpdate: new Date()
}
</script>
```

### 表格相关组件 (Table Components)

#### StandardDataTable
标准数据表格组件，提供完整的数据表格功能。

**功能特性:**
- 远程数据加载
- 查询栏集成
- 分页、排序、筛选
- 批量操作
- 列设置和密度调整
- 导出功能
- 选择功能
- 工具栏自定义
- 空状态处理
- 响应式设计

**使用示例:**
```vue
<template>
  <StandardDataTable
    :columns="columns"
    :load-data="loadData"
    :show-query-bar="true"
    :show-batch-delete="true"
    @selection-change="handleSelectionChange"
    @batch-delete="handleBatchDelete"
  >
    <template #query-fields="{ queryParams }">
      <n-form-item label="设备名称">
        <n-input v-model:value="queryParams.name" placeholder="请输入设备名称" />
      </n-form-item>
      <n-form-item label="状态">
        <n-select v-model:value="queryParams.status" :options="statusOptions" />
      </n-form-item>
    </template>
    
    <template #toolbar-left="{ selectedRows }">
      <n-button v-if="selectedRows.length > 0" type="primary">
        批量启动 ({{ selectedRows.length }})
      </n-button>
    </template>
  </StandardDataTable>
</template>

<script setup>
const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '设备名称', key: 'name', ellipsis: true },
  { title: '状态', key: 'status', render: (row) => renderStatus(row.status) },
  { title: '操作', key: 'actions', render: (row) => renderActions(row) }
]

const loadData = async (params) => {
  const response = await deviceAPI.getList(params)
  return {
    data: response.data.items,
    total: response.data.total
  }
}
</script>
```

### 表单相关组件 (Form Components)

#### StandardForm
标准表单组件，提供统一的表单生成和验证功能。

**功能特性:**
- 动态表单生成
- 多种字段类型支持
- 表单验证
- 字段联动
- 条件显示
- 分组支持
- 自定义组件
- 布局配置
- 响应式设计

**使用示例:**
```vue
<template>
  <StandardForm
    v-model="formData"
    :fields="formFields"
    title="设备信息"
    description="请填写设备的基本信息"
    @submit="handleSubmit"
    @field-change="handleFieldChange"
  >
    <template #field-custom-suffix="{ field, value }">
      <n-button size="small">验证</n-button>
    </template>
  </StandardForm>
</template>

<script setup>
const formData = ref({})

const formFields = [
  {
    name: 'name',
    label: '设备名称',
    type: 'input',
    required: true,
    placeholder: '请输入设备名称'
  },
  {
    name: 'type',
    label: '设备类型',
    type: 'select',
    required: true,
    options: [
      { label: '焊接设备', value: 'welding' },
      { label: '切割设备', value: 'cutting' }
    ]
  },
  {
    name: 'location',
    label: '设备位置',
    type: 'input',
    when: { field: 'type', value: 'welding' }
  },
  {
    type: 'divider',
    label: '技术参数'
  },
  {
    name: 'specs',
    label: '技术规格',
    type: 'group',
    fields: [
      {
        name: 'power',
        label: '功率',
        type: 'number',
        unit: 'W'
      },
      {
        name: 'voltage',
        label: '电压',
        type: 'number',
        unit: 'V'
      }
    ]
  }
]
</script>
```

## 字段类型支持

StandardForm 组件支持以下字段类型：

- `input` - 文本输入框
- `textarea` - 多行文本
- `password` - 密码输入框
- `number` - 数字输入框
- `select` - 下拉选择
- `switch` - 开关
- `date` - 日期选择器
- `time` - 时间选择器
- `radio` - 单选按钮组
- `checkbox` - 复选框组
- `slider` - 滑块
- `rate` - 评分
- `color` - 颜色选择器
- `upload` - 文件上传
- `group` - 字段分组
- `divider` - 分割线

## 组件配置

### 全局配置
```javascript
import { BUSINESS_COMPONENT_CONFIG } from '@/components/business'

// 修改默认配置
BUSINESS_COMPONENT_CONFIG.device.statusCard.defaultSize = 'large'
BUSINESS_COMPONENT_CONFIG.table.standardDataTable.defaultPageSize = 50
```

### 主题定制
```css
:root {
  /* 设备卡片主题 */
  --device-card-border-radius: 8px;
  --device-card-padding: 16px;
  --device-card-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  /* 表格主题 */
  --table-header-bg: #fafafa;
  --table-row-hover-bg: #f5f5f5;
  
  /* 表单主题 */
  --form-label-color: #333;
  --form-border-color: #d9d9d9;
}
```

## 开发规范

### 组件开发原则
1. **业务导向** - 组件应该解决具体的业务问题
2. **可配置性** - 提供丰富的配置选项
3. **可扩展性** - 支持插槽和自定义组件
4. **数据驱动** - 通过配置生成界面
5. **类型安全** - 提供完整的TypeScript支持

### 命名规范
- 组件名使用业务领域前缀
- 文件按业务领域分目录组织
- 事件名使用业务语义

### 数据格式规范
```javascript
// 设备数据格式
const deviceData = {
  id: string,           // 设备ID
  name: string,         // 设备名称
  status: string,       // 状态：active|inactive|maintenance|fault
  device_type: string,  // 类型：welding|cutting|assembly|inspection
  location?: string,    // 位置
  lastUpdate?: Date,    // 最后更新时间
  // 监控指标
  [metricKey]: number
}

// 表格列配置格式
const columnConfig = {
  title: string,        // 列标题
  key: string,          // 数据键
  width?: number,       // 列宽度
  ellipsis?: boolean,   // 是否省略
  sortable?: boolean,   // 是否可排序
  filterable?: boolean, // 是否可筛选
  render?: Function     // 自定义渲染
}

// 表单字段配置格式
const fieldConfig = {
  name: string,         // 字段名
  label: string,        // 字段标签
  type: string,         // 字段类型
  required?: boolean,   // 是否必填
  placeholder?: string, // 占位符
  options?: Array,      // 选项（select等）
  rules?: Array,        // 验证规则
  when?: Object,        // 条件显示
  onChange?: Function   // 变化回调
}
```

## 性能优化

### 懒加载
```javascript
// 按需加载业务组件
const DeviceStatusCard = defineAsyncComponent(() => 
  import('@/components/business/device/DeviceStatusCard.vue')
)
```

### 虚拟滚动
```vue
<!-- 大数据量表格启用虚拟滚动 -->
<StandardDataTable
  :virtual-scroll="true"
  :columns="columns"
  :load-data="loadData"
/>
```

### 缓存优化
```javascript
// 表格数据缓存
const { data, loading } = useAsyncData('device-list', loadData, {
  server: false,
  default: () => ({ data: [], total: 0 })
})
```

## 测试指南

### 单元测试
```javascript
import { mount } from '@vue/test-utils'
import DeviceStatusCard from '../DeviceStatusCard.vue'

describe('DeviceStatusCard', () => {
  const mockDevice = {
    id: 'DEV001',
    name: '测试设备',
    status: 'active',
    device_type: 'welding'
  }
  
  it('renders device information correctly', () => {
    const wrapper = mount(DeviceStatusCard, {
      props: { device: mockDevice }
    })
    
    expect(wrapper.find('.device-name').text()).toBe('测试设备')
    expect(wrapper.find('.device-status-tag').text()).toBe('运行中')
  })
  
  it('emits click event when clicked', async () => {
    const wrapper = mount(DeviceStatusCard, {
      props: { device: mockDevice, clickable: true }
    })
    
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

### 集成测试
```javascript
import { mount } from '@vue/test-utils'
import StandardDataTable from '../StandardDataTable.vue'

describe('StandardDataTable', () => {
  const mockLoadData = vi.fn().mockResolvedValue({
    data: [{ id: 1, name: '测试' }],
    total: 1
  })
  
  it('loads data on mount', async () => {
    mount(StandardDataTable, {
      props: {
        columns: [{ title: '名称', key: 'name' }],
        loadData: mockLoadData
      }
    })
    
    await nextTick()
    expect(mockLoadData).toHaveBeenCalled()
  })
})
```

## 贡献指南

1. 新增业务组件前先确认是否有复用价值
2. 遵循现有的设计规范和API风格
3. 提供完整的文档和示例
4. 编写单元测试和集成测试
5. 确保组件的可访问性
6. 更新相关的类型定义