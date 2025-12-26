# Deployment 部署工具

本目录包含项目的离线打包和版本管理工具。

## 📁 文件列表

### 🚀 核心脚本

| 文件 | 用途 | 说明 |
|------|------|------|
| **离线打包.bat** | 创建离线部署包 | 支持版本号和时间戳 |
| **管理打包版本.bat** | 版本管理工具 | 列表/删除/清理/压缩 |
| **release_automation.py** | 发布自动化 | 自动化发布流程 |
| **setup_git_hooks.py** | Git 钩子配置 | 代码提交规范 |

### 📚 文档

| 文件 | 内容 |
|------|------|
| **README.md** | 主文档（本文件） |
| **快速开始.md** | 一分钟上手指南 |
| **使用指南.md** | 完整使用说明 |
| **故障排除.md** | 常见问题解决 |

### ⚙️ 配置文件

| 文件 | 用途 |
|------|------|
| **deploy_exclude.txt** | 部署排除列表 |
| **exclude_packages.txt** | 包排除列表 |

## 🎯 快速开始

### 1. 创建离线部署包

```cmd
scripts\deployment\离线打包.bat
```

**输出**：`releases/offline_deploy_{版本号}_{时间戳}/`

### 2. 管理历史版本

```cmd
scripts\deployment\管理打包版本.bat
```

**功能**：
- 列出所有版本
- 查看版本详情
- 删除指定版本
- 清理旧版本
- 压缩版本
- 计算大小

### 3. 配置 Git 版本号

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# 再次打包（会使用 v1.0.0）
scripts\deployment\离线打包.bat
```

## 📊 版本命名规则

### 格式

```
offline_deploy_{版本号}_{时间戳}
```

### 示例

```
offline_deploy_1.0.0_20251118_143052
offline_deploy_1.2.3_20251118_150230
offline_deploy_2.0.0_20251119_091500
```

### 组成部分

- **版本号**：从 Git 标签获取（如 `v1.0.0`），无标签时使用 `v1.0.0`
- **时间戳**：`YYYYMMDD_HHMMSS` 格式

## 🔍 当前项目状态

**Git 标签**：❌ 无标签  
**默认版本**：v1.0.0  
**打包名称**：`offline_deploy_1.0.0_{时间戳}`

**建议**：立即创建第一个版本标签！

```bash
git tag -a v1.0.0 -m "设备监控系统 v1.0.0 - 首个正式版本"
git push origin v1.0.0
```

## 📖 文档导航

### 快速入门

1. **[快速开始](快速开始.md)** - 一分钟上手，快速创建第一个部署包
2. **[使用指南](使用指南.md)** - 完整的使用说明和最佳实践
3. **[故障排除](故障排除.md)** - 常见问题和解决方案

## 💡 使用场景

### 场景 1：首次打包

```cmd
# 1. 创建版本标签（可选但推荐）
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# 2. 运行打包
scripts\deployment\离线打包.bat

# 3. 输出
releases\offline_deploy_1.0.0_20251118_143052\
```

### 场景 2：版本迭代

```bash
# 修复 Bug
git tag -a v1.0.1 -m "Bug fixes"
git push origin v1.0.1
scripts\deployment\离线打包.bat
# 输出: offline_deploy_1.0.1_20251118_150000

# 新增功能
git tag -a v1.1.0 -m "New features"
git push origin v1.1.0
scripts\deployment\离线打包.bat
# 输出: offline_deploy_1.1.0_20251118_160000
```

### 场景 3：版本管理

```cmd
# 查看所有版本
管理打包版本.bat → [1] 列出所有版本

# 清理旧版本（保留最近5个）
管理打包版本.bat → [4] 清理旧版本 → 输入 5

# 压缩归档
管理打包版本.bat → [5] 压缩指定版本
```

## 🛠️ 高级功能

### 发布自动化

```bash
# 自动化发布流程
python scripts\deployment\release_automation.py release --type minor

# 功能：
# - 自动更新版本号
# - 生成变更日志
# - 创建 Git 标签
# - 运行测试
# - 构建项目
# - 推送到远程
```

### Git 钩子配置

```bash
# 配置 Git 钩子
python scripts\deployment\setup_git_hooks.py install

# 功能：
# - 提交消息验证
# - 代码检查
# - 预推送测试
```

## 📁 目录结构

```
deployment/
├── 📜 核心脚本
│   ├── 离线打包.bat                # 主打包脚本
│   ├── 管理打包版本.bat            # 版本管理工具
│   ├── release_automation.py      # 发布自动化
│   └── setup_git_hooks.py         # Git 钩子
├── 📚 文档
│   ├── README.md                  # 主文档（本文件）
│   ├── 快速开始.md                # 快速入门
│   ├── 使用指南.md                # 完整说明
│   └── 故障排除.md                # 问题解决
└── ⚙️ 配置
    ├── deploy_exclude.txt         # 排除配置
    └── exclude_packages.txt       # 包排除配置
```

## ⚠️ 注意事项

1. **版本号管理**
   - 使用 Git 标签管理版本
   - 遵循语义化版本规范
   - 标签必须以 'v' 开头

2. **磁盘空间**
   - 每个版本约 200-500 MB
   - 定期清理旧版本
   - 重要版本可压缩归档

3. **版本保留**
   - 开发环境：保留 3-5 个版本
   - 生产环境：保留当前 + 上一个稳定版

4. **Git 配置**
   - `releases/` 已添加到 .gitignore
   - 不会提交到版本库

## 🔗 相关链接

- [项目主文档](../../README.md)
- [部署指南](../../docs/DEPLOYMENT.md)
- [Scripts 目录](../README.md)

## 📞 技术支持

如遇问题：
1. 查看相关文档
2. 检查错误日志
3. 联系开发团队

---

**最后更新**: 2025-11-18  
**维护者**: DeviceMonitor 开发团队
