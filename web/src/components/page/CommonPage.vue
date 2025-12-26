<template>
  <AppPage :show-footer="showFooter">
    <header
      v-if="showHeader"
      mb-15
      min-h-45
      flex
      items-center
      justify-between
      px-15
      class="responsive-header"
    >
      <slot v-if="$slots.header" name="header" />
      <template v-else>
        <h2 flex-shrink-1 text-22 text-hex-333 font-normal dark:text-hex-ccc class="page-title">
          {{ title || route.meta?.title }}
        </h2>
        <div class="action-wrapper">
          <slot name="action" />
        </div>
      </template>
    </header>

    <n-card flex-1 rounded-10>
      <slot />
    </n-card>
  </AppPage>
</template>

<script setup>
import { useRoute } from 'vue-router'

defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
  showHeader: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: undefined,
  },
})
const route = useRoute()
</script>

<style scoped>
.responsive-header {
  flex-wrap: wrap;
  gap: 8px;
}

.page-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-wrapper {
  flex-shrink: 0;
  min-width: 0;
}

/* 小屏幕适配 */
@media (max-width: 768px) {
  .responsive-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .page-title {
    width: 100%;
    font-size: 18px;
  }

  .action-wrapper {
    width: 100%;
    overflow-x: auto;
  }

  .action-wrapper :deep(.flex) {
    flex-wrap: nowrap;
    min-width: max-content;
  }
}

/* 中等屏幕适配 */
@media (max-width: 1024px) and (min-width: 769px) {
  .action-wrapper :deep(.flex) {
    gap: 4px;
  }

  .action-wrapper :deep(.n-button) {
    padding: 0 8px;
  }

  .action-wrapper :deep(.hidden.sm\:inline) {
    display: none !important;
  }
}
</style>
