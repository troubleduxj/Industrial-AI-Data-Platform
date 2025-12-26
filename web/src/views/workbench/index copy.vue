<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
            <div></div>
          </div>
        </div>
      </n-card>
      <n-grid cols="2 s:2 m:3 l:3 xl:3 2xl:3" responsive="screen" :x-gap="12" :y-gap="8">
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/dashboard')">
            <div class="menu-item-icon" style="background: #1890ff">
              <Icon icon="ant-design:dashboard-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">监测看板</div>
              <div class="menu-item-description" style="text-align: center">
                实时监控设备状态和运行数据
              </div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/device')">
            <div class="menu-item-icon" style="background: #52c41a">
              <Icon icon="ant-design:appstore-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">设备管理</div>
              <div class="menu-item-description">管理和配置所有连接的设备</div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/device-monitoring')">
            <div class="menu-item-icon" style="background: #f5222d">
              <Icon icon="ant-design:monitor-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">设备监测</div>
              <div class="menu-item-description">实时监测设备运行状态和参数</div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/statistics')">
            <div class="menu-item-icon" style="background: #fa8c16">
              <Icon icon="ant-design:bar-chart-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">数据统计</div>
              <div class="menu-item-description">设备数据分析和统计报表</div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/alarm')">
            <div class="menu-item-icon" style="background: #722ed1">
              <Icon icon="ant-design:bell-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">告警中心</div>
              <div class="menu-item-description">设备异常告警和通知管理</div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/flow-settings')">
            <div class="menu-item-icon" style="background: #eb2f96">
              <Icon icon="ant-design:node-index-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">流程编排</div>
              <div class="menu-item-description">自动化流程配置和管理</div>
            </div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card class="menu-item-card" hoverable @click="handleCardClick('/ai-monitoring')">
            <div class="menu-item-icon" style="background: #13c2c2">
              <Icon icon="ant-design:robot-outlined" />
            </div>
            <div class="menu-item-content">
              <div class="menu-item-title">AI监测</div>
              <div class="menu-item-description">智能分析和预测性维护</div>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUserStore, useChatWidgetStore } from '@/store'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import UnifiedChatContainer from '@/components/chat-widget/UnifiedChatContainer.vue'
import SidebarTrigger from '@/components/chat-widget/SidebarTrigger.vue'
import { getCachedConfig } from '@/api/index.js'

const handleCardClick = (route) => {
  router.push(route)
}

const { t } = useI18n({ useScope: 'global' })
const router = useRouter()
const chatWidgetStore = useChatWidgetStore()

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_number_of_items'),
    value: '25',
  },
  {
    id: 1,
    label: t('views.workbench.label_upcoming'),
    value: '4/16',
  },
  {
    id: 2,
    label: t('views.workbench.label_information'),
    value: '12',
  },
])

// 菜单数据和处理函数已移至 UnifiedChatContainer 组件中

const userStore = useUserStore()

// 确保在workbench页面中显示边栏触发器
onMounted(async () => {
  // 设置为collapsed模式以显示SidebarTrigger
  chatWidgetStore.setDisplayMode('collapsed')

  // 保持获取 AI_ASSISTANT_ENABLED 配置的逻辑，但不影响页面显示
  try {
    const response = await getCachedConfig('AI_ASSISTANT_ENABLED')
    if (response.data && response.data.param_value === 'true') {
      console.log('AI Assistant is enabled.')
    } else {
      console.log('AI Assistant is disabled.')
    }
  } catch (error) {
    console.error('Failed to fetch AI_ASSISTANT_ENABLED config:', error)
  }
})
</script>

<style scoped>
.menu-item-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
}

.menu-item-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.menu-item-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 28px;
  color: #fff;
}

.menu-item-content {
  flex: 1;
}

.menu-item-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.menu-item-description {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}
</style>
