<template>
  <teleport to="body">
    <div
      v-if="visible"
      ref="menuContainer"
      class="context-menu"
      :style="{
        left: `${adjustedX}px`,
        top: `${adjustedY}px`,
        zIndex: 9999,
      }"
      @click.stop
      @contextmenu.prevent
    >
      <div class="menu-content">
        <template v-for="(item, index) in items" :key="index">
          <!-- 分割线 -->
          <div v-if="item.type === 'divider'" class="menu-divider"></div>

          <!-- 子菜单 -->
          <div
            v-else-if="item.children"
            class="submenu menu-item"
            :class="{
              disabled: item.disabled,
              active: hoveredIndex === index,
            }"
            @mouseenter="handleItemHover(index)"
            @mouseleave="handleItemLeave"
            @click="handleSubmenuClick(item, index)"
          >
            <div class="item-content">
              <span v-if="item.icon" class="item-icon">{{ item.icon }}</span>
              <span class="item-label">{{ item.label }}</span>
              <span class="submenu-arrow">▶</span>
            </div>

            <!-- 子菜单内容 -->
            <div v-if="expandedSubmenu === index" class="submenu-content" :style="submenuStyle">
              <template v-for="(subItem, subIndex) in item.children" :key="subIndex">
                <div v-if="subItem.type === 'divider'" class="menu-divider"></div>
                <div
                  v-else
                  class="menu-item"
                  :class="{
                    disabled: subItem.disabled,
                    dangerous: subItem.dangerous,
                    active: hoveredSubIndex === subIndex,
                  }"
                  @mouseenter="hoveredSubIndex = subIndex"
                  @mouseleave="hoveredSubIndex = -1"
                  @click="handleItemClick(subItem)"
                >
                  <div class="item-content">
                    <span v-if="subItem.icon" class="item-icon">{{ subItem.icon }}</span>
                    <span class="item-label">{{ subItem.label }}</span>
                    <span v-if="subItem.shortcut" class="item-shortcut">{{
                      subItem.shortcut
                    }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 普通菜单项 -->
          <div
            v-else
            class="menu-item"
            :class="{
              disabled: item.disabled,
              dangerous: item.dangerous,
              active: hoveredIndex === index,
              checked: item.checked,
            }"
            @mouseenter="handleItemHover(index)"
            @mouseleave="handleItemLeave"
            @click="handleItemClick(item)"
          >
            <div class="item-content">
              <span v-if="item.icon" class="item-icon">{{ item.icon }}</span>
              <span class="item-label">{{ item.label }}</span>
              <span v-if="item.shortcut" class="item-shortcut">{{ item.shortcut }}</span>
              <span v-if="item.checked" class="item-check">✓</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 遮罩层 -->
    <div
      v-if="visible"
      class="context-menu-overlay"
      @click="handleOverlayClick"
      @contextmenu.prevent="handleOverlayClick"
    ></div>
  </teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  // 是否显示
  visible: {
    type: Boolean,
    default: false,
  },

  // X坐标
  x: {
    type: Number,
    default: 0,
  },

  // Y坐标
  y: {
    type: Number,
    default: 0,
  },

  // 菜单项
  items: {
    type: Array,
    default: () => [],
  },

  // 最小宽度
  minWidth: {
    type: Number,
    default: 160,
  },

  // 最大宽度
  maxWidth: {
    type: Number,
    default: 300,
  },
})

// Emits
const emit = defineEmits(['select', 'close'])

// 响应式数据
const menuContainer = ref(null)
const hoveredIndex = ref(-1)
const hoveredSubIndex = ref(-1)
const expandedSubmenu = ref(-1)
const menuDimensions = ref({ width: 0, height: 0 })

// 计算属性
const adjustedX = computed(() => {
  if (!menuDimensions.value.width) return props.x

  const windowWidth = window.innerWidth
  const menuWidth = menuDimensions.value.width

  // 如果菜单超出右边界，向左调整
  if (props.x + menuWidth > windowWidth) {
    return Math.max(0, windowWidth - menuWidth - 10)
  }

  return props.x
})

const adjustedY = computed(() => {
  if (!menuDimensions.value.height) return props.y

  const windowHeight = window.innerHeight
  const menuHeight = menuDimensions.value.height

  // 如果菜单超出下边界，向上调整
  if (props.y + menuHeight > windowHeight) {
    return Math.max(0, windowHeight - menuHeight - 10)
  }

  return props.y
})

const submenuStyle = computed(() => {
  return {
    left: '100%',
    top: '0',
  }
})

// 方法
function handleItemClick(item) {
  if (item.disabled) return

  emit('select', item)

  // 如果不是切换类型的项目，关闭菜单
  if (!item.toggle) {
    emit('close')
  }
}

function handleSubmenuClick(item, index) {
  if (item.disabled) return

  if (expandedSubmenu.value === index) {
    expandedSubmenu.value = -1
  } else {
    expandedSubmenu.value = index
  }
}

function handleItemHover(index) {
  hoveredIndex.value = index

  // 如果当前项有子菜单，展开它
  const item = props.items[index]
  if (item && item.children) {
    expandedSubmenu.value = index
  } else {
    // 关闭其他子菜单
    expandedSubmenu.value = -1
  }
}

function handleItemLeave() {
  hoveredIndex.value = -1
}

function handleOverlayClick() {
  emit('close')
}

function handleKeyDown(event) {
  if (!props.visible) return

  switch (event.key) {
    case 'Escape':
      emit('close')
      break

    case 'ArrowDown':
      event.preventDefault()
      navigateDown()
      break

    case 'ArrowUp':
      event.preventDefault()
      navigateUp()
      break

    case 'ArrowRight':
      event.preventDefault()
      expandCurrentSubmenu()
      break

    case 'ArrowLeft':
      event.preventDefault()
      collapseCurrentSubmenu()
      break

    case 'Enter':
    case ' ':
      event.preventDefault()
      selectCurrentItem()
      break
  }
}

function navigateDown() {
  const validItems = props.items.filter((item) => item.type !== 'divider')
  if (validItems.length === 0) return

  let nextIndex = hoveredIndex.value + 1
  while (nextIndex < props.items.length) {
    const item = props.items[nextIndex]
    if (item.type !== 'divider' && !item.disabled) {
      hoveredIndex.value = nextIndex
      return
    }
    nextIndex++
  }

  // 循环到第一个有效项
  nextIndex = 0
  while (nextIndex < props.items.length) {
    const item = props.items[nextIndex]
    if (item.type !== 'divider' && !item.disabled) {
      hoveredIndex.value = nextIndex
      return
    }
    nextIndex++
  }
}

function navigateUp() {
  const validItems = props.items.filter((item) => item.type !== 'divider')
  if (validItems.length === 0) return

  let prevIndex = hoveredIndex.value - 1
  while (prevIndex >= 0) {
    const item = props.items[prevIndex]
    if (item.type !== 'divider' && !item.disabled) {
      hoveredIndex.value = prevIndex
      return
    }
    prevIndex--
  }

  // 循环到最后一个有效项
  prevIndex = props.items.length - 1
  while (prevIndex >= 0) {
    const item = props.items[prevIndex]
    if (item.type !== 'divider' && !item.disabled) {
      hoveredIndex.value = prevIndex
      return
    }
    prevIndex--
  }
}

function expandCurrentSubmenu() {
  if (hoveredIndex.value >= 0) {
    const item = props.items[hoveredIndex.value]
    if (item && item.children) {
      expandedSubmenu.value = hoveredIndex.value
      hoveredSubIndex.value = 0
    }
  }
}

function collapseCurrentSubmenu() {
  if (expandedSubmenu.value >= 0) {
    expandedSubmenu.value = -1
    hoveredSubIndex.value = -1
  }
}

function selectCurrentItem() {
  if (hoveredSubIndex.value >= 0 && expandedSubmenu.value >= 0) {
    // 选择子菜单项
    const parentItem = props.items[expandedSubmenu.value]
    const subItem = parentItem.children[hoveredSubIndex.value]
    if (subItem && !subItem.disabled) {
      handleItemClick(subItem)
    }
  } else if (hoveredIndex.value >= 0) {
    // 选择主菜单项
    const item = props.items[hoveredIndex.value]
    if (item && !item.disabled) {
      if (item.children) {
        handleSubmenuClick(item, hoveredIndex.value)
      } else {
        handleItemClick(item)
      }
    }
  }
}

function updateMenuDimensions() {
  nextTick(() => {
    if (menuContainer.value) {
      const rect = menuContainer.value.getBoundingClientRect()
      menuDimensions.value = {
        width: rect.width,
        height: rect.height,
      }
    }
  })
}

// 生命周期
onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})

// 监听器
watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      hoveredIndex.value = -1
      hoveredSubIndex.value = -1
      expandedSubmenu.value = -1
      updateMenuDimensions()
    }
  }
)

watch(
  () => props.items,
  () => {
    updateMenuDimensions()
  },
  { deep: true }
)
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 4px 0;
  min-width: 160px;
  max-width: 300px;
  z-index: 9999;
  user-select: none;
  font-size: 14px;
  animation: context-menu-appear 0.15s ease-out;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  background: transparent;
}

.menu-content {
  position: relative;
}

.menu-item {
  position: relative;
  padding: 0;
  margin: 0;
  cursor: pointer;
  transition: all 0.15s ease;
}

.menu-item:hover:not(.disabled) {
  background: #f5f5f5;
}

.menu-item.active:not(.disabled) {
  background: #e6f7ff;
}

.menu-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.menu-item.dangerous:hover:not(.disabled) {
  background: #fff2f0;
  color: #ff4d4f;
}

.menu-item.dangerous.active:not(.disabled) {
  background: #fff2f0;
  color: #ff4d4f;
}

.menu-item.checked {
  background: #f6ffed;
}

.item-content {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  gap: 8px;
  min-height: 32px;
}

.item-icon {
  font-size: 16px;
  width: 16px;
  text-align: center;
  flex-shrink: 0;
}

.item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-shortcut {
  font-size: 12px;
  color: #8c8c8c;
  font-family: 'Courier New', monospace;
  flex-shrink: 0;
}

.item-check {
  color: #52c41a;
  font-weight: bold;
  flex-shrink: 0;
}

.submenu-arrow {
  font-size: 10px;
  color: #8c8c8c;
  flex-shrink: 0;
  transform: rotate(0deg);
  transition: transform 0.15s ease;
}

.submenu {
  position: relative;
}

.submenu-content {
  position: absolute;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 4px 0;
  min-width: 160px;
  max-width: 300px;
  z-index: 10000;
  animation: submenu-appear 0.15s ease-out;
}

.menu-divider {
  height: 1px;
  background: #e8e8e8;
  margin: 4px 0;
}

/* 动画效果 */
@keyframes context-menu-appear {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes submenu-appear {
  from {
    opacity: 0;
    transform: scale(0.95) translateX(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateX(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .context-menu {
    min-width: 140px;
    max-width: 250px;
    font-size: 13px;
  }

  .item-content {
    padding: 6px 12px;
    min-height: 28px;
  }

  .item-icon {
    font-size: 14px;
    width: 14px;
  }

  .item-shortcut {
    font-size: 11px;
  }
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .context-menu,
  .submenu-content {
    background: #2f2f2f;
    border-color: #404040;
    color: #ffffff;
  }

  .menu-item:hover:not(.disabled) {
    background: #404040;
  }

  .menu-item.active:not(.disabled) {
    background: #1f3a8a;
  }

  .menu-item.dangerous:hover:not(.disabled),
  .menu-item.dangerous.active:not(.disabled) {
    background: #4a1a1a;
    color: #ff7875;
  }

  .menu-item.checked {
    background: #1f4a1f;
  }

  .item-shortcut {
    color: #a0a0a0;
  }

  .submenu-arrow {
    color: #a0a0a0;
  }

  .menu-divider {
    background: #404040;
  }
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .context-menu,
  .submenu-content {
    border-width: 2px;
    border-color: #000000;
  }

  .menu-item:hover:not(.disabled),
  .menu-item.active:not(.disabled) {
    background: #000000;
    color: #ffffff;
  }

  .menu-divider {
    background: #000000;
    height: 2px;
  }
}

/* 打印样式 */
@media print {
  .context-menu,
  .context-menu-overlay {
    display: none !important;
  }
}
</style>
