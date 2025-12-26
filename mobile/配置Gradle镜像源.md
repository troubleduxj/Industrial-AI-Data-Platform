# Gradle 镜像源配置指南

## 问题说明

在构建 Android 应用时，如果遇到以下错误：
```
Connection timed out: getsockopt
Could not GET 'https://maven.google.com/...'
```

这是因为无法访问 Google Maven 仓库。解决方法是配置镜像源。

---

## 解决方案 1：配置全局镜像（推荐）

已自动配置的 Gradle 全局配置文件：`C:\Users\duxia\.gradle\gradle.properties`

### 添加镜像仓库

在同一目录创建或编辑 `init.gradle`：

```gradle
allprojects {
    repositories {
        // 阿里云镜像
        maven { url 'https://maven.aliyun.com/repository/public' }
        maven { url 'https://maven.aliyun.com/repository/google' }
        maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
        
        // 腾讯云镜像（备用）
        maven { url 'https://mirrors.cloud.tencent.com/nexus/repository/maven-public/' }
        
        // 原始仓库（作为后备）
        google()
        mavenCentral()
    }
    
    buildscript {
        repositories {
            maven { url 'https://maven.aliyun.com/repository/public' }
            maven { url 'https://maven.aliyun.com/repository/google' }
            maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
            google()
            mavenCentral()
        }
    }
}
```

### 使用方法

1. 创建文件：`C:\Users\duxia\.gradle\init.gradle`
2. 复制上面的配置内容到文件中
3. 保存文件
4. 重新运行构建命令

---

## 解决方案 2：项目级配置

如果只想为当前项目配置，可以在项目中创建/编辑 Gradle 配置。

**注意**：NativeScript 项目的 Android 配置会在首次构建时生成，建议使用全局配置（方案 1）。

---

## 解决方案 3：配置代理

如果您有可用的代理，在 `C:\Users\duxia\.gradle\gradle.properties` 中添加：

```properties
# HTTP 代理
systemProp.http.proxyHost=your.proxy.host
systemProp.http.proxyPort=8080
systemProp.http.nonProxyHosts=localhost|127.0.0.1

# HTTPS 代理
systemProp.https.proxyHost=your.proxy.host
systemProp.https.proxyPort=8080
```

---

## 验证配置

配置完成后，运行以下命令测试：

```powershell
cd mobile
npx ns prepare android
```

如果成功，将看到依赖下载进度而不是超时错误。

---

## 其他镜像源（可选）

### 华为云镜像
```gradle
maven { url 'https://repo.huaweicloud.com/repository/maven/' }
```

### 中科大镜像
```gradle
maven { url 'https://mirrors.ustc.edu.cn/maven/maven2/' }
```

---

## 快速操作指令

创建 init.gradle（PowerShell）：

```powershell
# 创建 init.gradle 文件
$initGradleContent = @"
allprojects {
    repositories {
        maven { url 'https://maven.aliyun.com/repository/public' }
        maven { url 'https://maven.aliyun.com/repository/google' }
        maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
        google()
        mavenCentral()
    }
    buildscript {
        repositories {
            maven { url 'https://maven.aliyun.com/repository/public' }
            maven { url 'https://maven.aliyun.com/repository/google' }
            maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
            google()
            mavenCentral()
        }
    }
}
"@

$initGradleContent | Out-File -FilePath "$env:USERPROFILE\.gradle\init.gradle" -Encoding UTF8
Write-Host "init.gradle 创建成功！" -ForegroundColor Green
```

运行上面的 PowerShell 命令即可自动创建配置文件。

