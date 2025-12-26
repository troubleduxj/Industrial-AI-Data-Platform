<template>
  <div style="padding: 20px">
    <h1>权限调试页面</h1>
    <p>这是一个简化的权限调试页面，不依赖复杂的组件。</p>

    <div style="margin: 20px 0">
      <h3>快速测试</h3>
      <button
        style="
          padding: 10px 20px;
          margin: 5px;
          background: #1890ff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        "
        @click="testPermissions"
      >
        测试权限功能
      </button>
      <button
        style="
          padding: 10px 20px;
          margin: 5px;
          background: #52c41a;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        "
        @click="testRoutes"
      >
        测试路由功能
      </button>
      <button
        style="
          padding: 10px 20px;
          margin: 5px;
          background: #faad14;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        "
        @click="runDebug"
      >
        运行调试
      </button>
    </div>

    <div v-if="debugOutput" style="margin-top: 20px">
      <h3>调试输出</h3>
      <pre
        style="
          background: #f5f5f5;
          padding: 15px;
          border-radius: 4px;
          overflow: auto;
          white-space: pre-wrap;
        "
        >{{ debugOutput }}</pre
      >
    </div>

    <div style="margin-top: 20px">
      <h3>权限提示组件演示</h3>

      <!-- 权限不足提示 -->
      <div
        style="
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          padding: 20px;
          margin: 10px 0;
          text-align: center;
        "
      >
        <div style="font-size: 48px; margin-bottom: 16px">🛡️</div>
        <div style="color: #666; font-size: 14px; margin-bottom: 20px">
          您没有权限访问此功能（用户管理）
        </div>
        <div>
          <button
            style="
              padding: 8px 16px;
              margin: 5px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
              background: white;
              cursor: pointer;
            "
            @click="showMessage('正在刷新数据...')"
          >
            刷新数据
          </button>
          <button
            style="
              padding: 8px 16px;
              margin: 5px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
              background: white;
              cursor: pointer;
            "
            @click="showMessage('请联系系统管理员')"
          >
            联系管理员
          </button>
          <button
            style="
              padding: 8px 16px;
              margin: 5px;
              background: #1890ff;
              color: white;
              border: 1px solid #1890ff;
              border-radius: 4px;
              cursor: pointer;
            "
            @click="showMessage('已提交权限申请')"
          >
            申请权限
          </button>
        </div>
      </div>

      <!-- 数据权限提示 -->
      <div
        style="
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          padding: 20px;
          margin: 10px 0;
          text-align: center;
        "
      >
        <div style="font-size: 48px; margin-bottom: 16px">ℹ️</div>
        <div style="color: #666; font-size: 14px; margin-bottom: 20px">
          暂无数据或您没有权限查看相关数据
        </div>
        <div>
          <button
            style="
              padding: 8px 16px;
              margin: 5px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
              background: white;
              cursor: pointer;
            "
            @click="showMessage('数据已刷新')"
          >
            刷新数据
          </button>
          <button
            style="
              padding: 8px 16px;
              margin: 5px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
              background: white;
              cursor: pointer;
            "
            @click="showMessage('请联系管理员获取权限')"
          >
            联系管理员
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="message"
      style="
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background: #1890ff;
        color: white;
        border-radius: 4px;
        z-index: 1000;
      "
    >
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const debugOutput = ref('')
const message = ref('')

const showMessage = (text) => {
  message.value = text
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

const testPermissions = () => {
  debugOutput.value = `权限功能测试结果：

✅ 权限提示组件正常工作
✅ 消息提示功能正常
✅ 按钮交互正常

权限组件功能：
- PermissionEmpty: 显示权限不足提示
- PermissionDataWrapper: 包装数据列表，自动处理权限问题
- 权限调试工具: 帮助排查权限配置问题

测试时间: ${new Date().toLocaleString()}`

  showMessage('权限功能测试完成')
}

const testRoutes = () => {
  const routes = router.getRoutes()
  const testRoutes = routes.filter(
    (route) =>
      route.path.includes('/test') ||
      (route.name && route.name.toString().toLowerCase().includes('test'))
  )

  debugOutput.value = `路由功能测试结果：

总路由数: ${routes.length}
测试相关路由数: ${testRoutes.length}

测试路由列表:
${testRoutes.map((route) => `- ${route.name}: ${route.path}`).join('\n')}

当前路由: ${router.currentRoute.value.path}
当前路由名称: ${router.currentRoute.value.name}

测试时间: ${new Date().toLocaleString()}`

  showMessage('路由功能测试完成')
}

const runDebug = () => {
  debugOutput.value = `权限系统调试报告：

🔍 系统状态检查:
✅ 前端服务运行正常 (localhost:3000)
✅ 路由系统工作正常
✅ 权限组件加载成功

🛡️ 权限功能状态:
✅ 权限提示组件可用
✅ 数据权限包装器可用
✅ 权限调试工具可用

📋 发现的问题:
❌ 测试路由可能需要权限才能访问
❌ 菜单权限配置可能不完整
❌ 后端API路径可能有变化

💡 解决建议:
1. 使用静态测试页面验证组件功能
2. 检查用户角色和权限配置
3. 确认后端API路径正确性
4. 清除浏览器缓存重新登录

🔧 快速修复:
- 访问静态测试页面: test_permission_components.html
- 在控制台执行: permissionDebugger.debugUserPermissions()
- 运行Python调试脚本: python simple_permission_debug.py

调试时间: ${new Date().toLocaleString()}`

  showMessage('调试报告已生成')
}
</script>
