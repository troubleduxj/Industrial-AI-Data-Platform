# AI Monitor Common Components

## 目录结构

```
ai-monitor/
├── charts/           # 图表组件
│   ├── AIChart.vue          # 通用AI图表组件
│   ├── AnomalyChart.vue     # 异常检测图表
│   ├── TrendChart.vue       # 趋势预测图表
│   ├── HealthChart.vue      # 健康评分图表
│   └── index.js
├── forms/            # 表单组件
│   ├── ModelConfigForm.vue  # 模型配置表单
│   ├── ThresholdForm.vue    # 阈值配置表单
│   ├── AnnotationForm.vue   # 标注配置表单
│   └── index.js
├── common/           # 通用组件
│   ├── DataLoader.vue       # 数据加载器
│   ├── DeviceSelector.vue   # 设备选择器
│   ├── ModelSelector.vue    # 模型选择器
│   ├── StatusIndicator.vue  # 状态指示器
│   ├── AIInsight.vue        # AI洞察组件
│   └── index.js
└── index.js          # 统一导出
```

## 组件说明

### 图表组件 (charts/)
- **AIChart.vue**: 基础AI图表组件，提供统一的图表样式和交互
- **AnomalyChart.vue**: 异常检测专用图表
- **TrendChart.vue**: 趋势预测专用图表
- **HealthChart.vue**: 健康评分专用图表

### 表单组件 (forms/)
- **ModelConfigForm.vue**: 模型参数配置表单
- **ThresholdForm.vue**: 阈值设置表单
- **AnnotationForm.vue**: 数据标注配置表单

### 通用组件 (common/)
- **DataLoader.vue**: 统一的数据加载和状态管理
- **DeviceSelector.vue**: 设备选择下拉组件
- **ModelSelector.vue**: 模型选择下拉组件
- **StatusIndicator.vue**: AI监测状态指示器
- **AIInsight.vue**: AI洞察信息展示组件

## 使用方式

```javascript
// 导入单个组件
import { AIChart, DataLoader } from '@/components/ai-monitor'

// 导入分类组件
import { AnomalyChart, TrendChart } from '@/components/ai-monitor/charts'
import { ModelConfigForm } from '@/components/ai-monitor/forms'
import { DeviceSelector, StatusIndicator } from '@/components/ai-monitor/common'
```