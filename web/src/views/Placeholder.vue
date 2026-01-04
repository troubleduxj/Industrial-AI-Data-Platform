<template>
  <div class="placeholder-page">
    <n-result
      status="info"
      :title="title"
      :description="description"
    >
      <template #footer>
        <n-space vertical>
          <n-tag type="warning">Development in Progress</n-tag>
          <n-text depth="3">Path: {{ currentPath }}</n-text>
        </n-space>
      </template>
    </n-result>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { NResult, NTag, NText, NSpace } from 'naive-ui'

const route = useRoute()

const title = computed(() => (route.meta.title as string) || 'Feature Coming Soon')
const description = computed(() => `The module "${route.name as string}" is currently under construction.`)
const currentPath = computed(() => route.path)
</script>

<style scoped>
.placeholder-page {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
}
</style>
