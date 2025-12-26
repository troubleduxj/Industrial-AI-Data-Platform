<template>
  <ScrollX ref="scrollXRef" class="bg-white dark:bg-dark!">
    <n-tag
      v-for="tag in tagsStore.tags"
      ref="tabRefs"
      :key="tag.path"
      class="mx-5 cursor-pointer rounded-4 px-15 hover:color-primary"
      :type="tagsStore.activeTag === tag.path ? 'primary' : 'default'"
      :closable="tagsStore.tags.length > 1"
      @click="handleTagClick(tag.path)"
      @close.stop="tagsStore.removeTag(tag.path)"
      @contextmenu.prevent="handleContextMenu($event, tag)"
    >
      {{ tag.title }}
    </n-tag>
    <ContextMenu
      v-if="contextMenuOption.show"
      v-model:show="contextMenuOption.show"
      :current-path="contextMenuOption.currentPath"
      :x="contextMenuOption.x"
      :y="contextMenuOption.y"
    />
  </ScrollX>
</template>

<script setup>
import ContextMenu from './ContextMenu.vue'
import { useTagsStore } from '@/store'
import ScrollX from '@/components/common/ScrollX.vue'

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsStore()
const tabRefs = ref([])
const scrollXRef = ref(null)

const contextMenuOption = reactive({
  show: false,
  x: 0,
  y: 0,
  currentPath: '',
})

watch(
  () => route.path,
  () => {
    const { name, fullPath: path, meta } = route
    const title = meta?.title
    tagsStore.addTag({ name, path, meta, title })
  },
  { immediate: true }
)

watch(
  () => tagsStore.activeIndex,
  async (activeIndex) => {
    await nextTick()
    const activeTabElement = tabRefs.value[activeIndex]?.$el
    if (!activeTabElement) return
    // 使用scrollToElement方法滚动到指定元素
    scrollXRef.value?.scrollToElement(activeTabElement, 20)
  },
  { immediate: true }
)

const handleTagClick = (path) => {
  tagsStore.setActiveTag(path)
  router.push(path)
}

function showContextMenu() {
  contextMenuOption.show = true
}
function hideContextMenu() {
  contextMenuOption.show = false
}
function setContextMenu(x, y, currentPath) {
  Object.assign(contextMenuOption, { x, y, currentPath })
}

// 右击菜单
async function handleContextMenu(e, tagItem) {
  const { clientX, clientY } = e
  hideContextMenu()
  setContextMenu(clientX, clientY, tagItem.path)
  await nextTick()
  showContextMenu()
}
</script>

<style scoped>
/* 标签页容器样式 */
:deep(.scroll-x) {
  padding: 8px 16px;
  background: #fafafa;
  border-top: 1px solid #e8e8e8;
  border-bottom: 1px solid #e8e8e8;
}

/* 深色模式 */
:deep(.dark .scroll-x) {
  background: #1a1a1a;
  border-top: 1px solid #333;
  border-bottom: 1px solid #333;
}

/* 标签样式增强 */
:deep(.n-tag) {
  margin: 0 4px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

:deep(.n-tag:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 暗黑模式下的标签样式 */
:deep(.dark .n-tag--default) {
  background: #404040 !important;
  color: #e0e0e0 !important;
  border-color: #606060 !important;
}

:deep(.dark .n-tag--default:hover) {
  background: #4a4a4a !important;
  color: #ffffff !important;
  border-color: #707070 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* 暗黑模式下激活状态的标签 */
:deep(.dark .n-tag--primary) {
  background: var(--primary-color, #18a058);
  color: #ffffff;
  border-color: var(--primary-color, #18a058);
}

:deep(.dark .n-tag--primary:hover) {
  background: var(--primary-color-hover, #36ad6a);
  border-color: var(--primary-color-hover, #36ad6a);
  box-shadow: 0 2px 8px rgba(24, 160, 88, 0.3);
}

/* 关闭按钮样式 - 默认隐藏，悬浮时显示 */
:deep(.n-tag__close) {
  box-sizing: content-box;
  border-radius: 50%;
  font-size: 12px;
  padding: 2px;
  transform: scale(0.9);
  transform: translateX(5px);
  transition: all 0.3s;
  opacity: 0;
  visibility: hidden;
}

/* 标签悬浮时显示关闭按钮 */
:deep(.n-tag:hover .n-tag__close) {
  opacity: 1;
  visibility: visible;
}

/* 暗黑模式下的关闭按钮 */
:deep(.dark .n-tag__close) {
  color: #999;
}

:deep(.dark .n-tag__close:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

:deep(.dark .n-tag--primary .n-tag__close) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.dark .n-tag--primary .n-tag__close:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}
</style>
