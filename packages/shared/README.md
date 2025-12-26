# Shared Layer (cross-platform)

> 跨端共享层，复用 Web 与 NativeScript 的"无 UI 依赖"业务代码。

## 📁 目录结构

```
packages/shared/
├── types/         # TypeScript 类型定义（用户、设备、告警等）
├── utils/         # 纯工具函数（无 DOM/Node 依赖）
│   ├── validators.ts    # 类型检查与验证
│   ├── datetime.ts      # 日期时间处理
│   ├── format.ts        # 数据格式化
│   ├── helpers.ts       # 防抖、节流、深克隆等
│   └── storage.ts       # 跨端存储抽象
├── api/           # 跨端 API 客户端
│   ├── client.ts        # HTTP 客户端基类
│   ├── auth.ts          # 认证 API
│   ├── device.ts        # 设备 API
│   ├── alarm.ts         # 告警 API
│   ├── repair.ts        # 维修 API
│   └── index.ts         # 统一导出
└── README.md
```

## 🚀 快速开始

### Web 端接入

```typescript
// web/src/api/shared.ts
import { createApiServices } from '@/packages/shared/api';

const api = createApiServices({
  baseURL: import.meta.env.VITE_BASE_API || '/api/v2',
  getToken: () => localStorage.getItem('token'),
});

export default api;
```

使用示例：

```typescript
import api from '@/api/shared';

// 登录
const { data } = await api.auth.login({ username: 'admin', password: '123456' });

// 获取设备列表
const devices = await api.device.getDevices({ page: 1, pageSize: 20 });

// 获取告警统计
const stats = await api.alarm.getAlarmStats();
```

### NativeScript 端接入

```typescript
// mobile/src/services/api.ts
import { createApiServices } from '@shared/api';
import * as ApplicationSettings from '@nativescript/core/application-settings';

const api = createApiServices({
  baseURL: 'https://api.example.com/v2',
  getToken: () => ApplicationSettings.getString('token', ''),
});

export default api;
```

## 🛠️ 工具函数使用

```typescript
import {
  formatDate,
  formatFileSize,
  isValidEmail,
  debounce,
  throttle,
  deepClone,
  isEmpty,
} from '@shared/utils';

// 日期格式化
formatDate(new Date(), 'YYYY-MM-DD HH:mm:ss');

// 文件大小格式化
formatFileSize(1024 * 1024); // "1.0 MB"

// Email 验证
isValidEmail('user@example.com'); // true

// 防抖函数
const debouncedSearch = debounce((keyword) => {
  console.log('搜索:', keyword);
}, 300);
```

## 📦 类型定义

```typescript
import type {
  User,
  Device,
  Alarm,
  RepairRecord,
  Paginated,
  ApiResponse,
} from '@shared/types';

// 使用类型
const user: User = {
  id: 1,
  username: 'admin',
  nickname: '管理员',
  status: 'active',
};

const devices: Paginated<Device> = {
  items: [],
  total: 0,
  page: 1,
  pageSize: 20,
};
```

## ⚠️ 注意事项

1. **保持无 UI 依赖**：不要在 `shared` 层引入任何 UI 框架（Vue、NativeScript UI 组件等）
2. **避免平台特定 API**：不要使用 `window`、`document`、`localStorage` 等浏览器 API
3. **使用抽象层**：需要平台特定功能时，定义接口并在各端实现（如 `storage.ts`）
4. **类型优先**：充分利用 TypeScript 类型系统，确保跨端一致性

## 🔄 开发流程

1. **添加新类型**：在 `types/index.ts` 中定义
2. **添加新工具**：在 `utils/` 对应模块中实现
3. **添加新 API**：在 `api/` 中创建新模块，并在 `api/index.ts` 中导出
4. **更新文档**：在本 README 中添加使用示例
5. **测试验证**：在 Web 和 NativeScript 端分别验证

## 📚 进阶用法

### 自定义 API 请求

```typescript
import api from '@/api/shared';

// 使用原始客户端发起自定义请求
const customData = await api.client.get('/custom-endpoint', { param: 'value' });

// 带类型的请求
interface CustomResponse {
  id: number;
  name: string;
}
const typed = await api.client.get<CustomResponse>('/custom');
```

### 跨端存储

```typescript
// Web 端实现
import { createStorage } from '@shared/utils/storage';

const storage = createStorage({
  prefixKey: 'APP_',
  storage: localStorage, // 或 sessionStorage
});

storage.set('user', { id: 1, name: 'test' }, 3600); // 1小时过期
const user = storage.get('user');

// NativeScript 端实现
import { createStorage } from '@shared/utils/storage';
import * as ApplicationSettings from '@nativescript/core/application-settings';

const storage = createStorage({
  prefixKey: 'APP_',
  storage: {
    getItem: ApplicationSettings.getString,
    setItem: ApplicationSettings.setString,
    removeItem: ApplicationSettings.remove,
    clear: ApplicationSettings.clear,
  },
});
```
