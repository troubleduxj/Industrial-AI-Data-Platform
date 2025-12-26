# 通知管理模块 - 数据库迁移

## 文件说明

- `001_create_notification_tables.sql` - 创建通知表和用户通知状态表
- `002_insert_notification_menu.sql` - 插入通知管理菜单

## 执行步骤

```bash
# 连接数据库
psql -h 127.0.0.1 -U postgres -d devicemonitor

# 执行SQL
\i 001_create_notification_tables.sql
\i 002_insert_notification_menu.sql
```

## 表结构

### t_sys_notification (系统通知表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| title | VARCHAR(200) | 标题 |
| content | TEXT | 内容 |
| notification_type | VARCHAR(50) | 类型 |
| level | VARCHAR(20) | 级别 |
| scope | VARCHAR(20) | 发送范围 |
| target_roles | JSONB | 目标角色 |
| target_users | JSONB | 目标用户 |
| link_url | VARCHAR(500) | 跳转链接 |
| is_published | BOOLEAN | 是否发布 |
| publish_time | TIMESTAMP | 发布时间 |
| expire_time | TIMESTAMP | 过期时间 |

### t_sys_user_notification (用户通知状态表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| user_id | BIGINT | 用户ID |
| notification_id | BIGINT | 通知ID |
| is_read | BOOLEAN | 是否已读 |
| read_time | TIMESTAMP | 阅读时间 |
| is_deleted | BOOLEAN | 是否删除 |

## 通知类型

- `announcement` - 系统公告
- `alarm` - 报警通知
- `task` - 任务提醒
- `system` - 系统消息

## 通知级别

- `info` - 信息
- `warning` - 警告
- `error` - 错误

## 发送范围

- `all` - 全部用户
- `role` - 指定角色
- `user` - 指定用户
