# 权限控制使用指南

本文档说明如何在项目中正确使用权限控制组件和系统。

## 权限按钮组件 (PermissionButton)

### 基本用法

```vue
<template>
  <!-- API权限控制 -->
  <PermissionButton permission="GET /api/v2/users" @click="handleClick">
    查看用户
  </PermissionButton>
  
  <!-- 按钮级权限控制 -->
  <PermissionButton resource="user" action="create" type="primary" @click="createUser">
    创建用户
  </PermissionButton>
  
  <!-- 角色权限控制 -->
  <PermissionButton roles="admin" @click="adminFunction">
    管理员功能
  </PermissionButton>
</template>

<script setup>
import PermissionButton from '@/components/common/PermissionButton.vue'
</script>
```

### 权限类型

#### 1. API权限 (permission)
基于具体的API端点进行权限控制：

```vue
<PermissionButton permission="GET /api/v2/users">查看用户</PermissionButton>
<PermissionButton permission="POST /api/v2/users">创建用户</PermissionButton>
<PermissionButton permission="PUT /api/v2/users/{id}">更新用户</PermissionButton>
<PermissionButton permission="DELETE /api/v2/users/{id}">删除用户</PermissionButton>
```

#### 2. 按钮级权限 (resource + action)
基于资源和操作类型进行权限控制：

```vue
<PermissionButton resource="user" action="create">创建用户</PermissionButton>
<PermissionButton resource="user" action="read">查看用户</PermissionButton>
<PermissionButton resource="user" action="update">更新用户</PermissionButton>
<PermissionButton resource="user" action="delete">删除用户</PermissionButton>
```

#### 3. 角色权限 (roles)
基于用户角色进行权限控制：

```vue
<PermissionButton roles="admin">管理员功能</PermissionButton>
<PermissionButton roles="manager">管理员功能</PermissionButton>
<PermissionButton roles="['admin', 'manager']" permission-mode="any">任一角色</PermissionButton>
```

### 权限模式

- `any` (默认): 拥有任一权限即可访问
- `all`: 需要拥有所有权限才能访问

```vue
<PermissionButton 
  permission="['GET /api/v2/users', 'POST /api/v2/users']" 
  permission-mode="any"
>
  用户操作
</PermissionButton>

<PermissionButton 
  permission="['GET /api/v2/users', 'POST /api/v2/users']" 
  permission-mode="all"
>
  完整用户权限
</PermissionButton>
```

### 无权限时的行为

#### 隐藏按钮 (默认)
```vue
<PermissionButton permission="DELETE /api/v2/users/{id}" :hide-when-no-permission="true">
  删除用户
</PermissionButton>
```

#### 禁用按钮
```vue
<PermissionButton 
  permission="DELETE /api/v2/users/{id}" 
  :hide-when-no-permission="false"
  :disable-when-no-permission="true"
>
  删除用户
</PermissionButton>
```

## 权限指令 (v-permission)

### 基本用法

```vue
<template>
  <!-- API权限 -->
  <div v-permission="'GET /api/v2/users'">用户信息</div>
  
  <!-- 按钮权限 -->
  <div v-permission.button="{ resource: 'user', action: 'create' }">创建按钮</div>
  
  <!-- 角色权限 -->
  <div v-permission.role="'admin'">管理员内容</div>
  
  <!-- 隐藏而不是移除 -->
  <div v-permission.hide="'DELETE /api/v2/users/{id}'">删除功能</div>
  
  <!-- 禁用而不是隐藏 -->
  <button v-permission.disable="'DELETE /api/v2/users/{id}'">删除</button>
</template>
```

## 权限组合函数 (usePermission)

### 基本用法

```vue
<script setup>
import { usePermission } from '@/composables/usePermission'

const { 
  checkPermission, 
  checkButtonPermission, 
  checkRole,
  createButtonPermissions 
} = usePermission()

// 检查API权限
const canViewUsers = checkPermission('GET /api/v2/users')

// 检查按钮权限
const canCreateUser = checkButtonPermission('user', 'create')

// 检查角色权限
const isAdmin = checkRole('admin')

// 创建按钮权限配置
const userPermissions = createButtonPermissions('user')
// userPermissions.canCreate, userPermissions.canRead, etc.
</script>

<template>
  <div v-if="canViewUsers">用户列表</div>
  <button v-if="canCreateUser" @click="createUser">创建用户</button>
  <div v-if="isAdmin">管理员面板</div>
</template>
```

### 页面权限控制

```vue
<script setup>
import { usePagePermission } from '@/composables/usePermission'

const { canAccess, checkAccess } = usePagePermission('user:read')

// 在路由守卫中使用
onMounted(() => {
  if (!checkAccess()) {
    // 跳转到无权限页面
    router.push('/403')
  }
})
</script>
```

## 资源和操作映射

### 标准资源类型

| 资源 | 说明 | 示例操作 |
|------|------|----------|
| `user` | 用户管理 | create, read, update, delete |
| `role` | 角色管理 | create, read, update, delete, assign |
| `device` | 设备管理 | create, read, update, delete, control, monitor |
| `alarm` | 报警管理 | create, read, update, delete, handle |
| `ai-monitor` | AI监控 | create, read, update, delete, predict, train |
| `analysis` | 数据分析 | create, read, update, delete, export |
| `workflow` | 工作流 | create, read, update, delete, execute |
| `system` | 系统管理 | create, read, update, delete, config |

### 标准操作类型

| 操作 | 说明 | 对应HTTP方法 |
|------|------|--------------|
| `create` | 创建 | POST |
| `read` | 读取 | GET |
| `update` | 更新 | PUT/PATCH |
| `delete` | 删除 | DELETE |
| `export` | 导出 | GET |
| `import` | 导入 | POST |
| `execute` | 执行 | POST |
| `control` | 控制 | POST |
| `monitor` | 监控 | GET |
| `config` | 配置 | PUT |

## 迁移现有组件

### 1. 普通按钮替换

**替换前:**
```vue
<n-button type="primary" @click="createUser">创建用户</n-button>
<n-button @click="refreshData">刷新</n-button>
<n-button @click="exportData">导出</n-button>
```

**替换后:**
```vue
<PermissionButton resource="user" action="create" type="primary" @click="createUser">
  创建用户
</PermissionButton>
<PermissionButton resource="user" action="read" @click="refreshData">
  刷新
</PermissionButton>
<PermissionButton resource="user" action="export" @click="exportData">
  导出
</PermissionButton>
```

### 2. 添加导入语句

```vue
<script setup>
import PermissionButton from '@/components/common/PermissionButton.vue'
// ... 其他导入
</script>
```

### 3. 特殊情况处理

#### 模态框按钮
```vue
<!-- 取消按钮通常不需要权限控制 -->
<n-button @click="closeModal">取消</n-button>

<!-- 保存按钮需要权限控制 -->
<PermissionButton resource="user" action="update" type="primary" @click="saveUser">
  保存
</PermissionButton>
```

#### 导航按钮
```vue
<!-- 错误页面的返回按钮不需要权限控制 -->
<n-button @click="goHome">返回首页</n-button>

<!-- 业务页面的导航按钮可能需要权限控制 -->
<PermissionButton resource="dashboard" action="read" @click="goToDashboard">
  返回仪表板
</PermissionButton>
```

## 最佳实践

### 1. 权限粒度
- 页面级权限：控制整个页面的访问
- 功能级权限：控制页面内的功能模块
- 操作级权限：控制具体的操作按钮

### 2. 权限命名规范
- 资源名使用小写，多个单词用连字符分隔：`device-monitor`
- 操作名使用标准动词：`create`, `read`, `update`, `delete`
- API权限使用完整路径：`GET /api/v2/users`

### 3. 错误处理
- 无权限时提供友好的提示信息
- 避免暴露敏感的权限信息
- 提供权限申请的途径

### 4. 性能优化
- 权限检查结果会被缓存
- 避免在循环中进行复杂的权限检查
- 使用计算属性缓存权限状态

### 5. 测试
- 为权限控制编写单元测试
- 测试不同权限状态下的组件行为
- 验证权限变化时的响应式更新

## 常见问题

### Q: 如何处理动态权限？
A: 使用响应式的权限检查，权限变化时组件会自动更新：

```vue
<script setup>
const { checkPermission } = usePermission()
const canEdit = checkPermission('PUT /api/v2/users/{id}')
// canEdit 是响应式的，权限变化时会自动更新
</script>
```

### Q: 如何处理复杂的权限逻辑？
A: 使用自定义的权限检查函数：

```vue
<script setup>
const { createPermissionGuard } = usePermission()

const complexPermissionCheck = () => {
  // 复杂的权限逻辑
  return hasRole('admin') || (hasRole('manager') && hasPermission('special:action'))
}

const guard = createPermissionGuard(complexPermissionCheck, () => {
  message.warning('权限不足')
})
</script>
```

### Q: 如何在路由中使用权限控制？
A: 在路由守卫中使用权限检查：

```javascript
import { usePermission } from '@/composables/usePermission'

router.beforeEach((to, from, next) => {
  const { hasPermission } = usePermission()
  
  if (to.meta.permission && !hasPermission(to.meta.permission)) {
    next('/403')
  } else {
    next()
  }
})
```

## 总结

权限控制系统提供了灵活而强大的权限管理能力，通过合理使用权限按钮、权限指令和权限组合函数，可以实现细粒度的权限控制，提升系统的安全性和用户体验。