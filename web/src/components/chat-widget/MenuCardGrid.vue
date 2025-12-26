<template>
  <div class="menu-card-grid">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <n-input v-model:value="searchKeyword" placeholder="搜索功能..." clearable>
        <template #prefix>
          <Icon icon="mdi:magnify" />
        </template>
      </n-input>
    </div>

    <!-- 菜单网格 -->
    <div class="menu-content">
      <div v-if="filteredMenus.length === 0" class="empty-state">
        <div class="empty-icon">
          <Icon icon="mdi:apps" />
        </div>
        <p>未找到匹配的功能</p>
      </div>

      <div v-else class="menu-grid">
        <div
          v-for="menu in filteredMenus"
          :key="menu.id"
          class="menu-card"
          @click="handleMenuClick(menu)"
        >
          <div class="card-header">
            <div class="menu-icon" :style="{ background: getIconBackground(menu.iconColor) }">
              <Icon :icon="menu.icon" class="icon" />
            </div>
            <div v-if="menu.badge" class="menu-badge">
              <span>{{ menu.badge }}</span>
            </div>
          </div>

          <div class="card-content">
            <h4 class="menu-title">{{ menu.title }}</h4>
            <p class="menu-description">{{ menu.description }}</p>
          </div>

          <div v-if="menu.features" class="card-footer">
            <div class="feature-tags">
              <span v-for="feature in menu.features.slice(0, 2)" :key="feature" class="feature-tag">
                {{ feature }}
              </span>
              <span v-if="menu.features.length > 2" class="more-features">
                +{{ menu.features.length - 2 }}
              </span>
            </div>
          </div>

          <!-- 悬停效果 -->
          <div class="card-overlay">
            <div class="overlay-content">
              <Icon icon="mdi:arrow-right" class="arrow-icon" />
              <span>点击进入</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作栏 -->
    <div class="quick-actions">
      <n-button size="small" quaternary class="action-btn" @click="refreshMenus">
        <Icon icon="mdi:refresh" />
        刷新
      </n-button>

      <n-button size="small" quaternary class="action-btn" @click="showCustomizeDialog">
        <Icon icon="mdi:cog" />
        自定义
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChatWidgetStore } from '@/store'
import { Icon } from '@iconify/vue'
import { useRouter } from 'vue-router'

const chatWidgetStore = useChatWidgetStore()
const router = useRouter()
const searchKeyword = ref('')

// 扩展的菜单数据（包含更多功能）
const extendedMenus = computed(() => [
  ...chatWidgetStore.menuCards,
  {
    id: 5,
    title: '流程编排',
    description: '自动化流程配置和管理',
    icon: 'ant-design:node-index-outlined',
    iconColor: '#722ed1',
    route: '/workflow',
    features: ['自动化', '流程图', '任务调度'],
    badge: 'New',
  },
  {
    id: 6,
    title: '系统管理',
    description: '用户权限和系统配置管理',
    icon: 'ant-design:setting-outlined',
    iconColor: '#13c2c2',
    route: '/system',
    features: ['用户管理', '权限控制', '系统配置'],
  },
  {
    id: 7,
    title: '报表中心',
    description: '数据报表生成和导出',
    icon: 'ant-design:file-text-outlined',
    iconColor: '#fa541c',
    route: '/reports',
    features: ['报表生成', '数据导出', '定时任务'],
  },
  {
    id: 8,
    title: '日志审计',
    description: '系统日志查看和审计',
    icon: 'ant-design:audit-outlined',
    iconColor: '#096dd9',
    route: '/audit',
    features: ['操作日志', '安全审计', '日志分析'],
  },
])

// 过滤后的菜单
const filteredMenus = computed(() => {
  if (!searchKeyword.value) return extendedMenus.value

  return extendedMenus.value.filter(
    (menu) =>
      menu.title.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      menu.description.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      (menu.features &&
        menu.features.some((feature) =>
          feature.toLowerCase().includes(searchKeyword.value.toLowerCase())
        ))
  )
})

// 获取图标背景渐变
const getIconBackground = (color) => {
  const colorMap = {
    '#1890ff': 'linear-gradient(135deg, #1890ff, #40a9ff)',
    '#52c41a': 'linear-gradient(135deg, #52c41a, #73d13d)',
    '#fa8c16': 'linear-gradient(135deg, #fa8c16, #ffa940)',
    '#eb2f96': 'linear-gradient(135deg, #eb2f96, #f759ab)',
    '#722ed1': 'linear-gradient(135deg, #722ed1, #9254de)',
    '#13c2c2': 'linear-gradient(135deg, #13c2c2, #36cfc9)',
    '#fa541c': 'linear-gradient(135deg, #fa541c, #ff7a45)',
    '#096dd9': 'linear-gradient(135deg, #096dd9, #40a9ff)',
  }

  return colorMap[color] || `linear-gradient(135deg, ${color}, ${color}dd)`
}

// 处理菜单点击
const handleMenuClick = (menu) => {
  console.log('点击菜单:', menu.title)

  // 添加AI消息记录
  chatWidgetStore.addMessage({
    type: 'ai',
    content: `您点击了"${menu.title}"功能。${menu.description}`,
  })

  // 切换到聊天标签页
  chatWidgetStore.setActiveTab('chat')

  // 这里可以添加路由跳转逻辑
  // router.push(menu.route)
  window.$message?.info(`即将跳转到${menu.title}页面`)
}

// 刷新菜单
const refreshMenus = () => {
  window.$message?.success('菜单已刷新')
}

// 显示自定义对话框
const showCustomizeDialog = () => {
  window.$dialog?.info({
    title: '自定义菜单',
    content: '此功能正在开发中，敬请期待！',
    positiveText: '确定',
  })
}
</script>

<style scoped>
.menu-card-grid {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--n-card-color);
}

/* 搜索栏 */
.search-bar {
  padding: 16px;
  border-bottom: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

/* 菜单内容 */
.menu-content {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

/* 空状态 */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--n-color-embedded);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-icon .iconify {
  font-size: 32px;
  color: var(--n-text-color-disabled);
}

.empty-state p {
  margin: 0;
  color: var(--n-text-color-disabled);
  font-size: 14px;
}

/* 菜单网格 */
.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  height: 100%;
  overflow-y: auto;
  padding-bottom: 16px;
}

/* 菜单卡片 */
.menu-card {
  background: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  height: fit-content;
  min-height: 160px;
  display: flex;
  flex-direction: column;
}

.menu-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--n-primary-color);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.menu-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-color: var(--n-primary-color);
}

.menu-card:hover::before {
  transform: scaleX(1);
}

.menu-card:active {
  transform: translateY(-2px);
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.menu-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.menu-icon::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.menu-card:hover .menu-icon::before {
  opacity: 1;
}

.menu-icon .icon {
  font-size: 24px;
  color: white;
  z-index: 1;
}

.menu-badge {
  background: var(--n-error-color);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 卡片内容 */
.card-content {
  flex: 1;
  margin-bottom: 12px;
}

.menu-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--n-text-color);
  line-height: 1.4;
}

.menu-description {
  margin: 0;
  font-size: 13px;
  color: var(--n-text-color-disabled);
  line-height: 1.5;
}

/* 卡片底部 */
.card-footer {
  margin-top: auto;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feature-tag {
  background: var(--n-color-embedded);
  color: var(--n-text-color-disabled);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid var(--n-border-color);
}

.more-features {
  background: var(--n-primary-color-suppl);
  color: var(--n-primary-color);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}

/* 悬停覆盖层 */
.card-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--n-primary-color) ee, var(--n-primary-color-hover) ee);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s ease;
  backdrop-filter: blur(2px);
}

.menu-card:hover .card-overlay {
  opacity: 1;
}

.overlay-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  transform: translateY(10px);
  transition: transform 0.3s ease;
}

.menu-card:hover .overlay-content {
  transform: translateY(0);
}

.arrow-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.menu-card:hover .arrow-icon {
  transform: translateX(4px);
}

/* 快速操作栏 */
.quick-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--n-border-color);
  background: var(--n-color-embedded);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 滚动条样式 */
.menu-grid::-webkit-scrollbar {
  width: 4px;
}

.menu-grid::-webkit-scrollbar-track {
  background: transparent;
}

.menu-grid::-webkit-scrollbar-thumb {
  background: var(--n-scrollbar-color);
  border-radius: 2px;
}

.menu-grid::-webkit-scrollbar-thumb:hover {
  background: var(--n-scrollbar-color-hover);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .menu-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .menu-card {
    padding: 16px;
    min-height: 140px;
  }

  .menu-icon {
    width: 40px;
    height: 40px;
  }

  .menu-icon .icon {
    font-size: 20px;
  }

  .menu-title {
    font-size: 15px;
  }

  .menu-description {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .search-bar,
  .quick-actions {
    padding: 12px;
  }

  .menu-content {
    padding: 12px;
  }
}

/* 暗色主题适配 */
.dark .menu-card {
  background: var(--n-card-color);
  border-color: var(--n-border-color);
}

.dark .menu-card:hover {
  border-color: var(--n-primary-color);
}

.dark .feature-tag {
  background: var(--n-color-embedded);
  border-color: var(--n-border-color);
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .menu-card {
    border-width: 2px;
  }

  .feature-tag {
    border-width: 2px;
  }
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .menu-card,
  .card-overlay,
  .overlay-content,
  .arrow-icon,
  .menu-icon::before {
    transition: none;
  }

  .menu-card:hover {
    transform: none;
  }
}
</style>
