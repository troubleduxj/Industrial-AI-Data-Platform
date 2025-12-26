# 设备字段配置管理界面

## 📋 概述

设备字段配置管理界面提供可视化的方式来管理设备类型的监测字段配置，无需手动编写 SQL 或调用 API。

## 🎯 功能特性

- ✅ **设备类型选择** - 下拉选择要配置的设备类型
- ✅ **字段列表展示** - 表格形式展示所有字段配置
- ✅ **新增字段** - 通过表单创建新的字段配置
- ✅ **编辑字段** - 修改现有字段的配置
- ✅ **删除字段** - 删除不需要的字段配置
- ✅ **字段排序** - 控制字段在设备卡片中的显示顺序
- ✅ **图标配置** - 为字段设置 emoji 图标
- ✅ **颜色配置** - 为字段设置显示颜色
- ✅ **监测关键字段** - 标记哪些字段在设备卡片中显示
- ✅ **字段启用/禁用** - 控制字段是否生效

## 📦 文件清单

### 前端文件
```
web/src/
├── views/system/device-field/
│   └── index.vue                    # 主页面组件
├── api/
│   ├── device-v2.ts                 # 设备 API v2
│   └── device-field.ts              # 字段 API
└── types/
    └── device.ts                    # 类型定义
```

### 数据库文件
```
database/migrations/device-field-config-ui/
├── setup.sql                        # 数据库配置脚本
└── README.md                        # 本文档
```

### 文档文件
```
docs/device_test/
├── 字段配置管理界面设计方案.md
├── 字段配置管理界面-路由配置.md
└── 字段配置管理界面-部署指南.md
```

## 🚀 快速开始

### 1. 执行数据库脚本

```bash
psql -U postgres -d devicemonitor -f setup.sql
```

### 2. 添加路由配置

在 `web/src/router/index.ts` 中添加：

```typescript
{
  path: '/system/device-field',
  name: 'DeviceFieldConfig',
  component: () => import('@/views/system/device-field/index.vue'),
  meta: {
    title: '设备字段配置',
    icon: 'SettingsOutline',
    permission: 'system:device-field:view'
  }
}
```

### 3. 访问页面

登录系统后，访问：`系统管理 > 设备字段配置`

## 📖 使用指南

### 配置新设备类型的字段

1. **选择设备类型**
   - 在页面顶部的下拉框中选择要配置的设备类型

2. **新增字段**
   - 点击"新增字段"按钮
   - 填写字段信息：
     - 字段名称：中文显示名称（如"压力值"）
     - 字段代码：英文字段名（如"pressure"，需与 TDengine 表字段一致）
     - 字段类型：float/int/string/boolean
     - 单位：如 MPa、°C、mm/s
     - 排序：数字越小越靠前
     - 图标：emoji 图标（如 📊）
     - 颜色：十六进制颜色值
     - 监测关键字段：勾选后才会在设备卡片中显示
     - 启用：是否启用该字段
   - 点击"保存"

3. **编辑字段**
   - 在字段列表中找到要编辑的字段
   - 点击"编辑"按钮
   - 修改字段信息
   - 点击"保存"

4. **删除字段**
   - 在字段列表中找到要删除的字段
   - 点击"删除"按钮
   - 确认删除

5. **验证配置**
   - 刷新设备监测页面
   - 选择对应的设备类型
   - 查看设备卡片，应该能看到配置的字段

## 🔧 技术实现

### 前端技术栈
- Vue 3 + TypeScript
- Naive UI 组件库
- Pinia 状态管理
- Axios HTTP 客户端

### 后端 API
- FastAPI
- Tortoise ORM
- PostgreSQL

### 数据流程
```
前端页面
    ↓ 用户操作
API 调用
    ↓ HTTP 请求
后端处理
    ↓ 数据库操作
PostgreSQL (t_device_field 表)
    ↓ 配置生效
设备监测页面动态显示
```

## 📊 数据库表结构

### t_device_field 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| device_type_code | VARCHAR | 设备类型代码 |
| field_name | VARCHAR | 字段名称（中文） |
| field_code | VARCHAR | 字段代码（英文） |
| field_type | VARCHAR | 字段类型 |
| unit | VARCHAR | 单位 |
| sort_order | INTEGER | 排序 |
| display_config | JSONB | 显示配置 |
| field_category | VARCHAR | 字段分类 |
| description | TEXT | 描述 |
| is_monitoring_key | BOOLEAN | 是否监测关键字段 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 🎨 界面预览

```
┌─────────────────────────────────────────────────────────┐
│  设备字段配置管理                                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  设备类型: [智能压力传感器 ▼]  [+ 新增字段]  [刷新]    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 序号 │ 字段名 │ 字段码 │ 类型 │ 单位 │ 监测 │ 操作 │ │
│  ├──────┼────────┼────────┼──────┼──────┼──────┼──────┤ │
│  │  1   │📊压力值│pressure│float │ MPa  │  是  │编辑删│ │
│  │  2   │🌡️温度  │temp    │float │  °C  │  是  │编辑删│ │
│  │  3   │📳振动值│vibration│float│mm/s  │  是  │编辑删│ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🐛 故障排查

### 菜单不显示
- 检查数据库脚本是否执行成功
- 检查用户角色是否有权限
- 清除浏览器缓存

### API 调用失败
- 检查后端服务是否运行
- 检查 API 权限配置
- 查看后端日志

### 字段不显示
- 检查 `is_monitoring_key` 是否为 true
- 检查 `is_active` 是否为 true
- 检查字段代码是否与 TDengine 表字段一致

## 📚 相关文档

- [字段配置管理界面设计方案](../../docs/device_test/字段配置管理界面设计方案.md)
- [字段配置管理界面-部署指南](../../docs/device_test/字段配置管理界面-部署指南.md)
- [快速配置新设备类型字段](../../docs/device_test/快速配置新设备类型字段.md)

## 🤝 贡献

如有问题或建议，请提交 Issue 或 Pull Request。

## 📄 许可证

MIT License
