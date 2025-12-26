<template>
  <n-dropdown
    :options="options"
    placement="bottom-end"
    :show-arrow="false"
    trigger="click"
    @select="handleSelect"
  >
    <div
      class="avatar-container"
      :class="{ 'has-image': userStore.avatar, 'has-initials': !userStore.avatar }"
      flex
      cursor-pointer
      items-center
    >
      <img v-if="userStore.avatar" :src="userStore.avatar" class="user-avatar" />
      <div v-else class="default-avatar" :style="{ backgroundColor: 'var(--primary-color)' }">
        {{ getInitials(userStore.name) }}
      </div>
      <!-- 隐藏用户名文本，只显示头像 -->
      <!-- <span ml-10>{{ userStore.name }}</span> -->
    </div>
  </n-dropdown>
</template>

<script setup>
import { useUserStore, useThemeStore } from '@/store'
import { renderIcon } from '@/utils'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const themeStore = useThemeStore()
const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const options = [
  {
    label: t('header.label_profile'),
    key: 'profile',
    icon: renderIcon('mdi-account-arrow-right-outline', { size: '14px' }),
  },
  {
    label: t('header.label_logout'),
    key: 'logout',
    icon: renderIcon('mdi:exit-to-app', { size: '14px' }),
  },
]

/**
 * 获取用户名首字母
 * @param {string} name - 用户名
 * @returns {string} 首字母
 */
function getInitials(name) {
  if (!name) return 'U'
  const words = name.trim().split(' ')
  if (words.length === 1) {
    return words[0].charAt(0).toUpperCase()
  }
  return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase()
}

/**
 * 处理下拉菜单选择
 * @param {string} key - 选择的菜单项key
 */
function handleSelect(key) {
  if (key === 'profile') {
    router.push('/profile')
  } else if (key === 'logout') {
    $dialog.confirm({
      title: t('header.label_logout_dialog_title'),
      type: 'warning',
      content: t('header.text_logout_confirm'),
      confirm() {
        userStore.logout()
        $message.success(t('header.text_logout_success'))
      },
    })
  }
}
</script>

<style scoped>
.avatar-container {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

/* 当有头像图片时，外环使用主题色 */
.avatar-container.has-image {
  background-color: var(--primary-color);
}

/* 当没有头像图片时（显示字母），外环使用浅色 */
.avatar-container.has-initials {
  background-color: var(--primary-color-lighter);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

/* Apply a monochrome filter to the user's photo using the theme color */
img.user-avatar {
  background-color: var(--primary-color);
  mix-blend-mode: luminosity;
}

.avatar-container .default-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-color) !important;
  background-color: var(--primary-color) !important;
  color: white !important;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

.default-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px var(--primary-color-suppl);
}

/* 确保dropdown菜单不会超出视口 - 简化版本 */
:deep(.n-dropdown-menu) {
  min-width: 140px;
  max-width: 200px;
  /* 强制右对齐到视口边缘 */
  right: 10px !important;
  left: auto !important;
  /* 确保不超出视口 */
  transform: translateX(0) !important;
}

/* 当dropdown可能超出时，强制调整位置 */
:deep(.n-dropdown[data-placement*='end'] .n-dropdown-menu) {
  right: 10px !important;
  left: auto !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
  :deep(.n-dropdown-menu) {
    min-width: 120px;
    max-width: 180px;
    right: 8px !important;
  }
}

@media (max-width: 480px) {
  :deep(.n-dropdown-menu) {
    min-width: 100px;
    max-width: 150px;
    right: 6px !important;
  }
}
</style>
