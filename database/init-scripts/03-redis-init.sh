#!/bin/bash
# Redis 初始化脚本
# 设备监控系统 - 一步部署

echo "Starting Redis initialization..."

# 等待Redis服务启动
echo "Waiting for Redis to be ready..."
until redis-cli ping; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done

echo "Redis is ready!"

# 设置一些基础配置
redis-cli CONFIG SET save "900 1 300 10 60 10000"
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET timeout 300

# 创建一些基础的键值对
redis-cli SET "system:status" "initialized"
redis-cli SET "system:version" "1.0.0"
redis-cli SET "system:init_time" "$(date -Iseconds)"

# 设置设备状态缓存的默认过期时间（秒）
redis-cli SET "config:device_status_ttl" "300"
redis-cli SET "config:session_ttl" "3600"
redis-cli SET "config:cache_ttl" "1800"

# 创建一些测试数据
redis-cli HSET "device:DEVICE_001" "status" "online" "last_seen" "$(date -Iseconds)" "location" "Building_A_Floor_1"
redis-cli HSET "device:DEVICE_002" "status" "online" "last_seen" "$(date -Iseconds)" "location" "Building_A_Floor_2"
redis-cli HSET "device:DEVICE_003" "status" "online" "last_seen" "$(date -Iseconds)" "location" "Building_B_Floor_1"

# 设置设备状态过期时间（5分钟）
redis-cli EXPIRE "device:DEVICE_001" 300
redis-cli EXPIRE "device:DEVICE_002" 300
redis-cli EXPIRE "device:DEVICE_003" 300

# 创建设备组
redis-cli SADD "group:GROUP_A" "DEVICE_001" "DEVICE_002"
redis-cli SADD "group:GROUP_B" "DEVICE_003"

# 创建位置索引
redis-cli SADD "location:Building_A_Floor_1" "DEVICE_001"
redis-cli SADD "location:Building_A_Floor_2" "DEVICE_002"
redis-cli SADD "location:Building_B_Floor_1" "DEVICE_003"

# 设置系统统计信息
redis-cli SET "stats:total_devices" "3"
redis-cli SET "stats:online_devices" "3"
redis-cli SET "stats:offline_devices" "0"

# 创建告警配置
redis-cli HSET "alert:config" "temperature_max" "50" "temperature_min" "-10" "humidity_max" "90" "humidity_min" "10"

# 设置API限流配置
redis-cli SET "ratelimit:default" "100"  # 每分钟100次请求
redis-cli SET "ratelimit:admin" "1000"   # 管理员每分钟1000次请求

echo "Redis initialization completed successfully!"
echo "Initialized keys:"
redis-cli KEYS "*" | head -20
echo "Total keys created: $(redis-cli DBSIZE)"