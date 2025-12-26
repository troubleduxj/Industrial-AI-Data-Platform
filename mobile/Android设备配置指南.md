# Android 设备配置指南

## 问题说明

如果运行 `npm run android` 时出现以下错误：
```
Cannot find connected devices.
Emulator start failed with: No emulator image available...
```

**这不是 Java 环境问题！** 这是缺少运行中的 Android 设备（模拟器或真机）。

---

## ✅ 您的系统状态

### 已检测到的模拟器
1. **Medium Phone API 36.1** - Android API 36
2. **Pixel 6** - Android 13.0.0

### Java 环境
✅ Java 17 环境完全正常，可以正常打包

---

## 🚀 解决方案

### 方案 1：自动启动模拟器（推荐）

```powershell
cd mobile
npx ns run android --emulator
```

这个命令会：
1. 自动选择一个可用的模拟器
2. 启动模拟器
3. 构建并安装应用
4. 运行应用

### 方案 2：手动启动指定模拟器

```powershell
cd mobile

# 启动 Pixel 6 模拟器
npx ns run android --device Pixel_6

# 或启动 Medium Phone API 36.1
npx ns run android --device Medium_Phone_API_36.1
```

### 方案 3：使用 Android Studio 启动模拟器

1. 打开 Android Studio
2. 点击 **Tools** → **Device Manager**
3. 选择一个模拟器（如 Pixel 6）
4. 点击 ▶️ 启动按钮
5. 等待模拟器完全启动
6. 在终端运行：
   ```powershell
   cd mobile
   npm run android
   ```

### 方案 4：连接真机调试

如果有 Android 手机：

1. **开启开发者选项**：
   - 设置 → 关于手机 → 连续点击"版本号" 7 次
   
2. **开启 USB 调试**：
   - 设置 → 开发者选项 → USB 调试（开启）
   
3. **连接手机到电脑**（USB 线）

4. **验证连接**：
   ```powershell
   adb devices
   ```
   应该能看到设备列表

5. **运行应用**：
   ```powershell
   cd mobile
   npm run android
   ```

---

## 🔍 常用检查命令

### 查看所有可用的模拟器
```powershell
cd mobile
npx ns device android --available-devices
```

### 查看当前连接的设备
```powershell
cd mobile
npx ns device
```

### 查看 ADB 识别的设备
```powershell
adb devices
```

### 重启 ADB 服务（如果设备无法识别）
```powershell
adb kill-server
adb start-server
adb devices
```

---

## 🎯 首次运行建议

### 使用自动模拟器模式（最简单）

```powershell
cd D:\Cursor\Project\DeviceMonitorV2_20251013_V1\DeviceMonitorV2\mobile
npx ns run android --emulator
```

第一次运行会：
1. ✅ 自动选择可用模拟器
2. ✅ 启动模拟器（需要等待 1-2 分钟）
3. ✅ 编译应用
4. ✅ 安装到模拟器
5. ✅ 自动打开应用

**注意**：首次启动模拟器较慢，请耐心等待。

---

## 📋 模拟器启动时间

| 模拟器类型 | 首次启动 | 后续启动 |
|-----------|---------|---------|
| 冷启动 | 2-5 分钟 | 30-60 秒 |
| 已在后台运行 | 立即 | 立即 |

**建议**：开发时保持模拟器持续运行，可大幅提升开发效率。

---

## ⚠️ 常见问题

### 1. 模拟器启动失败

**症状**：模拟器黑屏或无限加载

**解决**：
```powershell
# 冷启动模拟器
$env:ANDROID_HOME\emulator\emulator.exe -avd Pixel_6 -wipe-data
```

### 2. 设备识别不到

**症状**：`adb devices` 显示 "unauthorized"

**解决**：
1. 在手机上点击"允许 USB 调试"
2. 如未弹出，运行：
   ```powershell
   adb kill-server
   adb start-server
   ```

### 3. 构建成功但应用未安装

**症状**：构建完成但模拟器没有应用图标

**解决**：
```powershell
cd mobile
npx ns clean
npx ns run android --emulator
```

---

## 🎉 验证构建成功

成功运行后，您会看到：

```
✔ Building project...
✔ Gradle build...
✔ Installing on device...
✔ Successfully synced application...
```

模拟器会自动打开应用界面。

---

## 📱 推荐的开发配置

### 日常开发流程

1. **启动模拟器**（保持运行）：
   ```powershell
   $env:ANDROID_HOME\emulator\emulator.exe -avd Pixel_6
   ```

2. **开发时运行**（热重载）：
   ```powershell
   cd mobile
   npm run android
   ```

3. **代码修改后**：应用会自动热重载，无需重启

---

## ✅ 总结

- ✅ **Java 17 环境正常** - 可以正常构建
- ✅ **模拟器已安装** - 有 2 个可用模拟器
- ✅ **只需启动设备** - 使用 `--emulator` 参数自动启动

**立即可用的命令**：
```powershell
cd D:\Cursor\Project\DeviceMonitorV2_20251013_V1\DeviceMonitorV2\mobile
npx ns run android --emulator
```

等待 1-2 分钟，应用即可在模拟器中运行！

