<template>
  <defs>
    <pattern id="grid-pattern" :width="gridSize" :height="gridSize" patternUnits="userSpaceOnUse">
      <path
        :d="`M ${gridSize} 0 L 0 0 0 ${gridSize}`"
        fill="none"
        :stroke="gridColor"
        :stroke-width="strokeWidth"
      />
    </pattern>
    <pattern
      v-if="showMajorGrid"
      id="major-grid-pattern"
      :width="majorGridSize"
      :height="majorGridSize"
      patternUnits="userSpaceOnUse"
    >
      <path
        :d="`M ${majorGridSize} 0 L 0 0 0 ${majorGridSize}`"
        fill="none"
        :stroke="majorGridColor"
        :stroke-width="majorStrokeWidth"
      />
    </pattern>
  </defs>

  <!-- Major grid background -->
  <rect
    v-if="showMajorGrid"
    x="-50%"
    y="-50%"
    width="200%"
    height="200%"
    fill="url(#major-grid-pattern)"
  />

  <!-- Minor grid background -->
  <rect x="-50%" y="-50%" width="200%" height="200%" fill="url(#grid-pattern)" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
const props = defineProps({
  // Grid configuration
  gridSize: {
    type: Number,
    default: 20,
  },

  // Grid colors
  gridColor: {
    type: String,
    default: '#e8e8e8',
  },

  // Stroke width
  strokeWidth: {
    type: Number,
    default: 1,
  },

  // Major grid
  showMajorGrid: {
    type: Boolean,
    default: true,
  },

  majorGridSize: {
    type: Number,
    default: 100,
  },

  majorGridColor: {
    type: String,
    default: '#d0d0d0',
  },

  majorStrokeWidth: {
    type: Number,
    default: 1.5,
  },
})
</script>

<style scoped>
/* Grid styles are handled via SVG patterns */
</style>
