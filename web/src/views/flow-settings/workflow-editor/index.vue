<template>
  <div class="workflow-editor-container">
    <div v-if="loading" class="loading-container">
      <n-spin size="large" :show="loading">
        <template #description> 正在跳转到工作流编辑器... </template>
        <div style="height: 200px"></div>
      </n-spin>
    </div>
    <div v-else-if="success" class="success-container">
      <div class="success-content">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="#52c41a">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
            />
          </svg>
        </div>
        <h2 class="success-title">跳转成功！</h2>
        <p class="success-description">
          工作流编辑器已在新标签页中打开，您可以继续在当前页面进行其他操作。
        </p>
        <n-button type="primary" class="retry-button" @click="redirectAgain">
          重新打开工作流编辑器
        </n-button>
      </div>
    </div>
    <div v-else-if="error" class="error-container">
      <n-alert title="跳转失败" type="error" :show-icon="true" :closable="false">
        {{ error }}
      </n-alert>
      <n-button type="primary" class="retry-button" @click="redirectToWorkflowEditor">
        重试
      </n-button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system-v2'
import { useMessage } from 'naive-ui'

export default {
  name: 'WorkflowEditor',
  setup() {
    const loading = ref(true)
    const success = ref(false)
    const error = ref('')
    const message = useMessage()
    let workflowUrl = ''

    // 获取系统参数并跳转
    const redirectToWorkflowEditor = async () => {
      try {
        loading.value = true

        // 调用系统参数API获取workflow_editor_addr
        const response = await systemApi.getSystemParamList({ param_key: 'workflow_editor_addr' })

        if (response && response.data) {
          // 查找workflow_editor_addr参数
          const workflowEditorParam = response.data.find(
            (param) => param.param_key === 'workflow_editor_addr'
          )

          if (workflowEditorParam && workflowEditorParam.param_value) {
            const url = workflowEditorParam.param_value

            // 验证URL格式
            if (isValidUrl(url)) {
              // 保存URL用于重新打开
              workflowUrl = url
              // 在新标签页中打开指定URL
              window.open(url, '_blank')
              // 设置成功状态
              success.value = true
              // 显示成功消息
              message.success('工作流编辑器已在新标签页中打开')
            } else {
              throw new Error('工作流编辑器地址格式不正确')
            }
          } else {
            throw new Error('未找到工作流编辑器地址配置(workflow_editor_addr)')
          }
        } else {
          throw new Error('获取系统参数失败')
        }
      } catch (err) {
        console.error('跳转到工作流编辑器失败:', err)
        error.value = err.message || '跳转失败，请检查系统配置'
        message.error(error.value)
      } finally {
        loading.value = false
      }
    }

    // 验证URL格式
    const isValidUrl = (string) => {
      try {
        new URL(string)
        return true
      } catch (_) {
        return false
      }
    }

    // 重新打开工作流编辑器
    const redirectAgain = () => {
      if (workflowUrl) {
        window.open(workflowUrl, '_blank')
        message.success('工作流编辑器已重新在新标签页中打开')
      }
    }

    onMounted(() => {
      redirectToWorkflowEditor()
    })

    return {
      loading,
      success,
      error,
      redirectToWorkflowEditor,
      redirectAgain,
    }
  },
}
</script>

<style scoped>
.workflow-editor-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.loading-container,
.success-container,
.error-container {
  width: 100%;
  max-width: 500px;
  padding: 40px;
  text-align: center;
}

.success-content {
  background: white;
  border-radius: 16px;
  padding: 48px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.success-icon {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.success-icon svg {
  filter: drop-shadow(0 4px 8px rgba(82, 196, 26, 0.3));
  animation: successPulse 2s ease-in-out infinite;
}

@keyframes successPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.success-title {
  color: #262626;
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 16px 0;
  line-height: 1.4;
}

.success-description {
  color: #595959;
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 32px 0;
}

.retry-button {
  margin-top: 16px;
  padding: 8px 24px;
  height: auto;
  border-radius: 8px;
  font-weight: 500;
}

.error-container {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  align-items: center;
  justify-content: center;
}

.loading-container {
  width: 100%;
  height: 100%;
}

.error-container {
  max-width: 500px;
  width: 100%;
}
</style>
