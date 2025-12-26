# 数据库初始化脚本

这个目录包含了设备监控系统一步部署时使用的数据库初始化脚本。

## 脚本说明

### 01-postgresql-init.sql
**PostgreSQL 数据库初始化脚本**

- **功能**: 初始化PostgreSQL主数据库
- **执行时机**: PostgreSQL容器启动时自动执行
- **主要操作**:
  - 创建devicemonitor数据库
  - 安装必要的PostgreSQL扩展
  - 创建基础表结构（users, devices等）
  - 创建索引和触发器
  - 插入默认管理员用户
  - 创建测试连接函数

**默认管理员账户**:
- 用户名: `admin`
- 邮箱: `admin@devicemonitor.com`
- 密码: `admin123` (请在生产环境中修改)

### 02-tdengine-init.sql
**TDengine 时序数据库初始化脚本**

- **功能**: 初始化TDengine时序数据库
- **执行时机**: TDengine容器启动后手动执行或应用启动时执行
- **主要操作**:
  - 创建devicemonitor数据库
  - 创建设备数据超级表(device_data)
  - 创建设备状态超级表(device_status)
  - 创建设备事件超级表(device_events)
  - 创建系统监控超级表(system_metrics)
  - 创建示例设备表和数据

**创建的超级表**:
- `device_data`: 设备传感器数据
- `device_status`: 设备在线状态和系统信息
- `device_events`: 设备事件日志
- `system_metrics`: 系统监控指标

### 03-redis-init.sh
**Redis 缓存数据库初始化脚本**

- **功能**: 初始化Redis缓存配置和基础数据
- **执行时机**: Redis容器启动后执行
- **主要操作**:
  - 配置Redis基础参数
  - 设置缓存策略和过期时间
  - 创建设备状态缓存
  - 设置设备分组信息
  - 配置API限流参数
  - 创建告警配置

**缓存配置**:
- 设备状态TTL: 300秒
- 会话TTL: 3600秒
- 通用缓存TTL: 1800秒

## 使用方法

### 自动执行（推荐）
使用一步部署脚本时，这些初始化脚本会自动执行：

```bash
# Windows
.\deploy-all-in-one.ps1 start

# Linux
./deploy-all-in-one.sh start
```

### 手动执行

#### PostgreSQL
```bash
# 进入PostgreSQL容器
docker exec -it devicemonitor_postgres psql -U postgres

# 执行初始化脚本
\i /docker-entrypoint-initdb.d/01-postgresql-init.sql
```

#### TDengine
```bash
# 进入TDengine容器
docker exec -it devicemonitor_tdengine taos

# 执行初始化脚本
source /init-scripts/02-tdengine-init.sql;
```

#### Redis
```bash
# 进入Redis容器
docker exec -it devicemonitor_redis bash

# 执行初始化脚本
/init-scripts/03-redis-init.sh
```

## 数据库连接信息

### PostgreSQL
- **主机**: localhost
- **端口**: 5432
- **数据库**: devicemonitor
- **用户名**: postgres
- **密码**: DeviceMonitor2024!

### TDengine
- **主机**: localhost
- **端口**: 6041
- **数据库**: devicemonitor
- **用户名**: root
- **密码**: taosdata

### Redis
- **主机**: localhost
- **端口**: 6379
- **密码**: DeviceMonitor2024!

## 注意事项

1. **生产环境安全**:
   - 修改默认密码
   - 限制数据库访问权限
   - 启用SSL/TLS加密

2. **数据持久化**:
   - PostgreSQL数据存储在 `postgres_data` 卷中
   - TDengine数据存储在 `tdengine_data` 卷中
   - Redis数据存储在 `redis_data` 卷中

3. **备份策略**:
   - 定期备份PostgreSQL数据
   - TDengine数据可通过导出功能备份
   - Redis数据可通过RDB/AOF备份

4. **监控和维护**:
   - 监控数据库连接数
   - 定期清理过期数据
   - 监控磁盘空间使用

## 故障排除

### PostgreSQL初始化失败
```bash
# 检查容器日志
docker logs devicemonitor_postgres

# 检查数据库连接
docker exec devicemonitor_postgres pg_isready -U postgres
```

### TDengine初始化失败
```bash
# 检查容器日志
docker logs devicemonitor_tdengine

# 检查TDengine服务状态
docker exec devicemonitor_tdengine systemctl status taosd
```

### Redis初始化失败
```bash
# 检查容器日志
docker logs devicemonitor_redis

# 检查Redis连接
docker exec devicemonitor_redis redis-cli ping
```

## 扩展和自定义

如需添加自定义初始化脚本：

1. 在此目录创建新的脚本文件
2. 使用数字前缀确保执行顺序（如 `04-custom-init.sql`）
3. 在docker-compose.yml中添加相应的卷挂载
4. 更新此README文档

## 版本历史

- **v1.0.0**: 初始版本，包含基础的三个数据库初始化脚本