<template>
  <router-view v-slot="{ Component, route }">
    <!-- [Final Debug Step] Removing transition to isolate the issue -->
    <keep-alive :include="keepAliveRouteNames">
      <component :is="Component" :key="route.meta.keepAlive ? route.name : route.path" />
    </keep-alive>
  </router-view>
</template>

<script setup>
import { computed } from 'vue'
import { useTagsStore } from '@/store/modules/tags'

const tagsStore = useTagsStore()

const keepAliveRouteNames = computed(() => {
  return tagsStore.tags.filter((route) => route.meta?.keepAlive).map((route) => route.name)
})
</script>
