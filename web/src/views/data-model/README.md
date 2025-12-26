# 数据模型管理模块

本模块实现了基于元数据驱动的设备数据模型管理系统。

## 📁 目录结构

```
data-model/
├── config/              # 模型配置管理
│   └── index.vue       # 数据模型CRUD页面
├── mapping/            # 字段映射管理
│   └── index.vue       # PostgreSQL ↔ TDengine 字段映射
├── preview/            # 数据预览与测试
│   └── index.vue       # 查询测试和数据预览
├── route.js            # 路由配置
└── README.md          # 本文件
```

## 🎯 功能概览

### 1. 模型配置管理 (`config/index.vue`)

**功能**:
- ✅ 数据模型列表查询（分页、筛选、排序）
- ✅ 新建/编辑数据模型
- ✅ 删除数据模型
- ✅ 激活/停用模型
- ✅ 字段选择（Transfer组件）
- ✅ 支持3种模型类型：realtime、statistics、ai_analysis

**技术栈**:
- Vue 3 Composition API
- Naive UI (NTable, NForm, NModal, NTransfer)
- API v2 (dataModelApi)

### 2. 字段映射管理 (`mapping/index.vue`)

**功能**:
- ✅ 字段映射列表查询
- ✅ 新增/编辑字段映射
- ✅ PostgreSQL字段 → TDengine列 映射
- ✅ 6种数据转换规则：
  1. Expression - 表达式转换
  2. Mapping - 值映射
  3. Range Limit - 范围限制
  4. Unit - 单位转换
  5. Round - 四舍五入
  6. Composite - 组合转换

**技术栈**:
- Vue 3 Composition API
- Naive UI (NDynamicInput, NInputNumber)
- 动态表单生成

### 3. 数据预览与测试 (`preview/index.vue`)

**功能**:
- ✅ 模型选择和信息展示
- ✅ 查询参数配置（设备、时间范围、分页）
- ✅ 实时数据查询
- ✅ 统计数据查询（时间间隔、分组）
- ✅ 表格视图（动态列生成）
- ✅ 图表视图（ECharts集成）
- ✅ SQL预览和复制
- ✅ 执行日志查看
- ✅ 数据导出（CSV）

**技术栈**:
- Vue 3 Composition API
- Naive UI (NLayout, NTabs, NDataTable)
- ECharts 图表库

## 🚀 使用说明

### 路由配置

路由已在 `route.js` 中定义，会被自动加载到主路由系统：

```javascript
/data-model
  ├── /config      # 模型配置管理
  ├── /mapping     # 字段映射管理
  └── /preview     # 预览与测试
```

### API集成

所有页面使用统一的API客户端：

```javascript
import { dataModelApi } from '@/api/v2/data-model'

// 使用示例
const response = await dataModelApi.getModels(params)
```

### 数据库菜单

菜单需要在数据库中创建，执行以下脚本：

```bash
# 方法1: 使用Python
cd database/migrations/device-data-model
python execute_menu_migration.py

# 方法2: 使用psql
psql -h 127.0.0.1 -U postgres -d devicemonitor -f 008_create_frontend_menu.sql
```

## 📝 开发规范

### 代码风格

- 使用 Vue 3 `<script setup>` 语法
- 使用 Composition API (ref, reactive, computed)
- 组件使用 PascalCase 命名
- 事件处理函数使用 `handle` 前缀
- API调用使用 async/await

### 错误处理

```javascript
try {
  const response = await dataModelApi.getModels()
  if (response.success) {
    // 处理成功
  } else {
    message.error(response.message || '操作失败')
  }
} catch (error) {
  message.error('网络错误：' + (error.message || '未知错误'))
}
```

### 表单验证

```javascript
const formRules = {
  field_name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' }
  ]
}

// 提交前验证
await formRef.value?.validate()
```

## 🔗 相关文档

### 使用指南
- [三模块使用指南](../../../docs/device-data-model/数据模型管理三模块使用指南.md) ⭐ 推荐阅读
- [三模块快速参考](../../../docs/device-data-model/三模块快速参考.md) - 简明版
- [三模块关系图解](../../../docs/device-data-model/三模块关系图解.md) - 可视化

### TDengine集成
- [TDengine字段同步功能说明](../../../docs/device-data-model/TDengine字段同步功能说明.md)
- [TDengine字段同步-前端集成说明](../../../docs/device-data-model/TDengine字段同步-前端集成说明.md)
- [TDengine字段同步功能实现总结](../../../docs/device-data-model/TDengine字段同步功能实现总结.md)

### 技术文档
- [API接口文档](../../../docs/device-data-model/API接口文档.md)
- [设计方案总览](../../../docs/device-data-model/00-设计方案总览.md)
- [Phase3实施指南](../../../docs/device-data-model/Phase3实施指南.md)
- [前端菜单规划](../../../docs/device-data-model/08-前端菜单规划建议.md)

## ✅ 完成状态

- [x] 路由配置
- [x] API客户端
- [x] 模型配置管理页面
- [x] 字段映射管理页面
- [x] 数据预览页面
- [x] 转换规则编辑器（集成在mapping中）
- [x] SQL语法高亮（使用n-code组件）
- [ ] 数据库菜单执行（需要手动执行）
- [ ] 测试验收

## 🐛 已知问题

1. 数据库连接失败 - 需要确保PostgreSQL服务运行
2. 菜单未显示 - 需要执行数据库菜单脚本
3. 权限未分配 - 需要为用户角色分配菜单权限

## 📞 支持

如有问题，请参考：
- [故障排查指南](../../../docs/device-data-model/Phase3实施指南.md#故障排查)
- [实施检查清单](../../../docs/device-data-model/实施检查清单.md)

