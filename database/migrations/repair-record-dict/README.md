# 维修记录字典数据

## 概述

本迁移脚本为设备维修记录页面创建数据字典，将原本硬编码的选项数据改为可配置的字典数据，便于后续维护和扩展。

## 包含的字典类型

| 字典代码 | 字典名称 | 数据项数量 | 说明 |
|---------|---------|-----------|------|
| `repair_device_category` | 维修设备类别 | 7 | 焊机类型等设备类别 |
| `device_brand` | 设备品牌 | 13 | 国内外主流焊机品牌 |
| `repair_fault_reason` | 故障原因 | 10 | 故障原因分类 |
| `repair_damage_category` | 损坏类别 | 5 | 损坏类型，用于责任判定 |

## 执行方式

### 方式一：使用Python脚本（推荐）

```bash
cd database/migrations/repair-record-dict
python apply_repair_dicts.py
```

### 方式二：直接执行SQL

```bash
# PostgreSQL
psql -h 127.0.0.1 -U postgres -d devicemonitor -f 001_create_repair_dicts.sql
```

## 前端使用

### 1. 引入API

```javascript
import { repairDictApi } from '@/api/repair-dict'

// 获取单个字典
const categories = await repairDictApi.getDeviceCategories()
const brands = await repairDictApi.getDeviceBrands()
const faultReasons = await repairDictApi.getFaultReasons()
const damageCategories = await repairDictApi.getDamageCategories()

// 批量获取所有字典
const allDict = await repairDictApi.getAllDictData()
```

### 2. 使用Composable（推荐）

```vue
<script setup>
import { useRepairDictOptions } from './composables/useRepairDictOptions'

// 自动加载字典数据
const {
  categoryOptions,
  brandOptions,
  faultReasonOptions,
  damageCategoryOptions,
  loading,
  refresh,
} = useRepairDictOptions()

// 带"全部"选项（用于搜索筛选）
const {
  categoryOptions: searchCategoryOptions,
  brandOptions: searchBrandOptions,
} = useRepairDictOptions({ withAllOption: true })
</script>

<template>
  <NSelect v-model:value="form.category" :options="categoryOptions" />
  <NSelect v-model:value="form.brand" :options="brandOptions" />
</template>
```

## 字典数据详情

### 设备类别 (repair_device_category)

| 标签 | 值 | 说明 |
|-----|---|------|
| 二氧化碳保护焊机 | 二氧化碳保护焊机 | CO2气体保护焊机 |
| 氩弧焊机 | 氩弧焊机 | TIG/氩弧焊机 |
| 电焊机 | 电焊机 | 手工电弧焊机 |
| 等离子切割机 | 等离子切割机 | 等离子切割设备 |
| 埋弧焊机 | 埋弧焊机 | 埋弧自动焊机 |
| 点焊机 | 点焊机 | 电阻点焊机 |
| 激光焊机 | 激光焊机 | 激光焊接设备 |

### 设备品牌 (device_brand)

| 标签 | 值 | 说明 |
|-----|---|------|
| 松下 | 松下 | Panasonic 日本品牌 |
| 林肯 | 林肯 | Lincoln Electric 美国品牌 |
| 米勒 | 米勒 | Miller 美国品牌 |
| 伊萨 | 伊萨 | ESAB 瑞典品牌 |
| 福尼斯 | 福尼斯 | Fronius 奥地利品牌 |
| OTC | OTC | OTC/大阪变压器 日本品牌 |
| 奥太 | 奥太 | 山东奥太电气 |
| 瑞凌 | 瑞凌 | 深圳瑞凌实业 |
| 佳士 | 佳士 | 深圳佳士科技 |
| 时代 | 时代 | 北京时代科技 |
| 凯尔达 | 凯尔达 | 杭州凯尔达 |
| 华意隆 | 华意隆 | 深圳华意隆 |
| 其他 | 其他 | 其他品牌 |

### 故障原因 (repair_fault_reason)

| 标签 | 值 | 说明 |
|-----|---|------|
| 操作不当 | 操作不当 | 人员操作失误导致的故障 |
| 老化磨损 | 老化磨损 | 设备长期使用导致的自然磨损 |
| 环境因素 | 环境因素 | 温度、湿度、灰尘等环境因素 |
| 设备缺陷 | 设备缺陷 | 设备本身设计或制造缺陷 |
| 维护不当 | 维护不当 | 日常维护保养不到位 |
| 电源问题 | 电源问题 | 电压不稳、电源故障等 |
| 过载使用 | 过载使用 | 超负荷运行导致的故障 |
| 配件损坏 | 配件损坏 | 易损件或配件损坏 |
| 外力损坏 | 外力损坏 | 碰撞、跌落等外力造成 |
| 其他原因 | 其他原因 | 其他未分类原因 |

### 损坏类别 (repair_damage_category)

| 标签 | 值 | 说明 |
|-----|---|------|
| 正常损坏 | 正常损坏 | 正常使用过程中的自然损耗 |
| 非正常损坏 | 非正常损坏 | 非正常使用导致的损坏 |
| 人为损坏 | 人为损坏 | 人为因素造成的损坏，需追责 |
| 意外损坏 | 意外损坏 | 不可预见的意外事故造成 |
| 质量问题 | 质量问题 | 产品质量问题导致的损坏 |

## 管理字典数据

字典数据可以通过系统管理 > 字典管理界面进行维护：

1. 添加新选项
2. 修改现有选项
3. 调整排序
4. 启用/禁用选项

## 注意事项

1. 修改字典数据后，前端会在5分钟内自动刷新（缓存过期）
2. 如需立即生效，可调用 `repairDictApi.clearCache()` 清除缓存
3. 删除字典选项前，请确认没有历史数据使用该值
