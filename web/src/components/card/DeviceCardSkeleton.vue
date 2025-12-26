<!-- web/src/components/card/DeviceCardSkeleton.vue -->
<template>
  <NCard class="device-card-skeleton">
    <div class="skeleton-header">
      <div class="skeleton-title"></div>
      <div class="skeleton-tag"></div>
    </div>
    <div class="skeleton-status"></div>
    <div class="skeleton-data">
      <div class="skeleton-row"></div>
      <div class="skeleton-row"></div>
    </div>
    <div class="skeleton-location"></div>
    <div class="skeleton-actions">
      <div class="skeleton-button"></div>
      <div class="skeleton-button"></div>
    </div>
  </NCard>
</template>

<script setup>
import { NCard } from 'naive-ui'
</script>

<style scoped>
.device-card-skeleton {
  border-left: 4px solid #e0e0e0;
}
.device-card-skeleton :deep(.n-card__content) {
  padding: 14px !important;
}

@keyframes skeleton-pulse {
  0% {
    background-color: #f0f0f0;
  }
  50% {
    background-color: #e0e0e0;
  }
  100% {
    background-color: #f0f0f0;
  }
}

.skeleton-header,
.skeleton-data,
.skeleton-actions {
  margin-bottom: 10px;
}

.skeleton-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.skeleton-data,
.skeleton-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-title {
  width: 60%;
  height: 20px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 4px;
}
.skeleton-tag {
  width: 50px;
  height: 20px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 4px;
}
.skeleton-status {
  width: 80px;
  height: 24px;
  margin-bottom: 10px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 4px;
}
.skeleton-row {
  width: 100%;
  height: 16px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 4px;
}
.skeleton-location {
  width: 70%;
  height: 14px;
  margin-bottom: 10px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 4px;
}
.skeleton-button {
  width: 100%;
  height: 32px;
  animation: skeleton-pulse 1.5s infinite ease-in-out;
  border-radius: 8px;
}
</style>
