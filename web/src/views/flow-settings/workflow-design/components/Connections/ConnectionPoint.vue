<template>
  <div
    class="connection-point"
    :class="{
      input: type === 'input',
      output: type === 'output',
      active: isActive,
      connected: isConnected,
      hover: isHover,
      compatible: isCompatible,
      incompatible: isIncompatible,
    }"
    :style="pointStyle"
    @mousedown.stop="handleMouseDown"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @click.stop="handleClick"
  >
    <!-- Connection dot -->
    <div class="connection-dot" :style="dotStyle">
      <div v-if="isActive || isConnected" class="connection-inner"></div>
    </div>

    <!-- Connection label -->
    <div v-if="label" class="connection-label" :class="{ visible: showLabel || isHover }">
      {{ label }}
    </div>

    <!-- Data type indicator -->
    <div v-if="dataType && showDataType" class="data-type-indicator">
      {{ getDataTypeLabel(dataType) }}
    </div>

    <!-- Connection count -->
    <div v-if="connectionCount > 0" class="connection-count">
      {{ connectionCount }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
const props = defineProps({
  // Connection point type
  type: {
    type: String,
    required: true,
    validator: (value: string) => ['input', 'output'].includes(value),
  },

  // Connection point position
  position: {
    type: String,
    default: 'right',
    validator: (value: string) => ['top', 'right', 'bottom', 'left'].includes(value),
  },

  // Connection point label
  label: {
    type: String,
    default: '',
  },

  // Data type
  dataType: {
    type: String,
    default: 'any',
  },

  // Connection point color
  color: {
    type: String,
    default: '#1890ff',
  },

  // Size of the connection point
  size: {
    type: Number,
    default: 12,
  },

  // Whether the point is active (being dragged)
  isActive: {
    type: Boolean,
    default: false,
  },

  // Whether the point has connections
  isConnected: {
    type: Boolean,
    default: false,
  },

  // Whether the point is being hovered
  isHover: {
    type: Boolean,
    default: false,
  },

  // Whether the point is compatible with current drag
  isCompatible: {
    type: Boolean,
    default: false,
  },

  // Whether the point is incompatible with current drag
  isIncompatible: {
    type: Boolean,
    default: false,
  },

  // Number of connections
  connectionCount: {
    type: Number,
    default: 0,
  },

  // Whether to show label always
  showLabel: {
    type: Boolean,
    default: false,
  },

  // Whether to show data type
  showDataType: {
    type: Boolean,
    default: false,
  },

  // Custom offset
  offset: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },
})

// Emits
const emit = defineEmits(['mousedown', 'mouseenter', 'mouseleave', 'click'])

// Computed properties
const pointStyle = computed(() => {
  const baseStyle = {
    transform: `translate(${props.offset.x}px, ${props.offset.y}px)`,
  }

  // Position-based styling
  switch (props.position) {
    case 'top':
      return {
        ...baseStyle,
        top: `-${props.size / 2}px`,
        left: '50%',
        transform: `translate(-50%, 0) translate(${props.offset.x}px, ${props.offset.y}px)`,
      }
    case 'bottom':
      return {
        ...baseStyle,
        bottom: `-${props.size / 2}px`,
        left: '50%',
        transform: `translate(-50%, 0) translate(${props.offset.x}px, ${props.offset.y}px)`,
      }
    case 'left':
      return {
        ...baseStyle,
        left: `-${props.size / 2}px`,
        top: '50%',
        transform: `translate(0, -50%) translate(${props.offset.x}px, ${props.offset.y}px)`,
      }
    case 'right':
    default:
      return {
        ...baseStyle,
        right: `-${props.size / 2}px`,
        top: '50%',
        transform: `translate(0, -50%) translate(${props.offset.x}px, ${props.offset.y}px)`,
      }
  }
})

const dotStyle = computed(() => {
  return {
    width: `${props.size}px`,
    height: `${props.size}px`,
    borderColor: props.color,
    backgroundColor: props.isConnected || props.isActive ? props.color : 'white',
  }
})

// Methods
function handleMouseDown(event) {
  emit('mousedown', {
    type: props.type,
    position: props.position,
    dataType: props.dataType,
    event,
  })
}

function handleMouseEnter(event) {
  emit('mouseenter', {
    type: props.type,
    position: props.position,
    dataType: props.dataType,
    event,
  })
}

function handleMouseLeave(event) {
  emit('mouseleave', {
    type: props.type,
    position: props.position,
    dataType: props.dataType,
    event,
  })
}

function handleClick(event) {
  emit('click', {
    type: props.type,
    position: props.position,
    dataType: props.dataType,
    event,
  })
}

function getDataTypeLabel(type) {
  const labels = {
    any: 'Any',
    string: 'Str',
    number: 'Num',
    boolean: 'Bool',
    object: 'Obj',
    array: 'Arr',
    date: 'Date',
    file: 'File',
    image: 'Img',
    json: 'JSON',
    xml: 'XML',
    csv: 'CSV',
  }
  return labels[type] || type.toUpperCase()
}
</script>

<style scoped>
.connection-point {
  position: absolute;
  display: flex;
  align-items: center;
  cursor: crosshair;
  z-index: 10;
  transition: all 0.2s ease;
}

.connection-point.input {
  flex-direction: row-reverse;
}

.connection-point.output {
  flex-direction: row;
}

.connection-point.active {
  z-index: 20;
}

.connection-point.compatible {
  transform: scale(1.2);
}

.connection-point.incompatible {
  opacity: 0.5;
  cursor: not-allowed;
}

.connection-dot {
  border: 2px solid #1890ff;
  border-radius: 50%;
  background: white;
  transition: all 0.2s ease;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.connection-point:hover .connection-dot,
.connection-point.hover .connection-dot {
  transform: scale(1.2);
  box-shadow: 0 0 8px rgba(24, 144, 255, 0.4);
}

.connection-point.active .connection-dot {
  transform: scale(1.3);
  box-shadow: 0 0 12px rgba(24, 144, 255, 0.6);
}

.connection-point.compatible .connection-dot {
  border-color: #52c41a;
  background: #52c41a;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.4);
}

.connection-point.incompatible .connection-dot {
  border-color: #ff4d4f;
  background: #ff4d4f;
}

.connection-inner {
  width: 4px;
  height: 4px;
  background: white;
  border-radius: 50%;
}

.connection-label {
  font-size: 10px;
  color: #595959;
  font-weight: 500;
  white-space: nowrap;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  margin: 0 6px;
  opacity: 0;
  transform: translateY(-2px);
  transition: all 0.2s ease;
  pointer-events: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.connection-label.visible {
  opacity: 1;
  transform: translateY(0);
}

.connection-point.input .connection-label {
  order: -1;
}

.data-type-indicator {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 8px;
  color: #8c8c8c;
  background: #f5f5f5;
  padding: 1px 4px;
  border-radius: 2px;
  font-weight: 500;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.connection-point:hover .data-type-indicator,
.connection-point.hover .data-type-indicator {
  opacity: 1;
}

.connection-count {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 14px;
  height: 14px;
  background: #ff4d4f;
  color: white;
  font-size: 8px;
  font-weight: 600;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid white;
}

/* Position-specific label positioning */
.connection-point[style*='top:'] .connection-label {
  margin: 6px 0;
}

.connection-point[style*='bottom:'] .connection-label {
  margin: 6px 0;
}

.connection-point[style*='left:'] .connection-label {
  margin: 0 6px;
}

.connection-point[style*='right:'] .connection-label {
  margin: 0 6px;
}

/* Animation for connection establishment */
@keyframes connectionPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

.connection-point.connected .connection-dot {
  animation: connectionPulse 2s ease-in-out infinite;
}
</style>
