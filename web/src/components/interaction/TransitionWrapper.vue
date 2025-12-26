<template>
  <transition
    :name="transitionName"
    :mode="mode"
    :duration="duration"
    :css="css"
    :appear="appear"
    @before-enter="handleBeforeEnter"
    @enter="handleEnter"
    @after-enter="handleAfterEnter"
    @before-leave="handleBeforeLeave"
    @leave="handleLeave"
    @after-leave="handleAfterLeave"
  >
    <slot />
  </transition>
</template>

<script setup>
import { computed } from 'vue'

/**
 * 过渡动画包装器组件
 * 提供统一的过渡动画效果
 *
 * @component TransitionWrapper
 * @example
 * <TransitionWrapper type="fade" :duration="300">
 *   <div v-if="show">内容</div>
 * </TransitionWrapper>
 */

const props = defineProps({
  // 过渡类型
  type: {
    type: String,
    default: 'fade',
    validator: (value) =>
      [
        'fade',
        'slide-up',
        'slide-down',
        'slide-left',
        'slide-right',
        'scale',
        'zoom',
        'flip',
        'bounce',
        'elastic',
        'rotate',
      ].includes(value),
  },

  // 过渡模式
  mode: {
    type: String,
    default: '',
    validator: (value) => ['', 'in-out', 'out-in'].includes(value),
  },

  // 动画持续时间
  duration: {
    type: [Number, Object],
    default: 300,
  },

  // 是否使用CSS过渡
  css: {
    type: Boolean,
    default: true,
  },

  // 是否在初始渲染时应用过渡
  appear: {
    type: Boolean,
    default: false,
  },

  // 动画缓动函数
  easing: {
    type: String,
    default: 'ease',
    validator: (value) =>
      ['ease', 'ease-in', 'ease-out', 'ease-in-out', 'linear', 'bounce', 'elastic'].includes(value),
  },

  // 延迟时间
  delay: {
    type: Number,
    default: 0,
  },

  // 自定义过渡名称
  customName: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'before-enter',
  'enter',
  'after-enter',
  'before-leave',
  'leave',
  'after-leave',
])

// 计算过渡名称
const transitionName = computed(() => {
  if (props.customName) {
    return props.customName
  }

  return `transition-${props.type}`
})

// 事件处理
function handleBeforeEnter(el) {
  if (props.delay > 0) {
    el.style.animationDelay = `${props.delay}ms`
  }
  emit('before-enter', el)
}

function handleEnter(el, done) {
  emit('enter', el, done)
  if (!props.css) {
    done()
  }
}

function handleAfterEnter(el) {
  if (props.delay > 0) {
    el.style.animationDelay = ''
  }
  emit('after-enter', el)
}

function handleBeforeLeave(el) {
  emit('before-leave', el)
}

function handleLeave(el, done) {
  emit('leave', el, done)
  if (!props.css) {
    done()
  }
}

function handleAfterLeave(el) {
  emit('after-leave', el)
}
</script>

<style scoped>
/* 淡入淡出 */
.transition-fade-enter-active,
.transition-fade-leave-active {
  transition: opacity v-bind(duration + 'ms') v-bind(easing);
}

.transition-fade-enter-from,
.transition-fade-leave-to {
  opacity: 0;
}

/* 向上滑动 */
.transition-slide-up-enter-active,
.transition-slide-up-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.transition-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 向下滑动 */
.transition-slide-down-enter-active,
.transition-slide-down-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-slide-down-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.transition-slide-down-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 向左滑动 */
.transition-slide-left-enter-active,
.transition-slide-left-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-slide-left-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.transition-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 向右滑动 */
.transition-slide-right-enter-active,
.transition-slide-right-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-slide-right-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.transition-slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 缩放 */
.transition-scale-enter-active,
.transition-scale-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-scale-enter-from,
.transition-scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

/* 放大 */
.transition-zoom-enter-active,
.transition-zoom-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-zoom-enter-from,
.transition-zoom-leave-to {
  opacity: 0;
  transform: scale(1.1);
}

/* 翻转 */
.transition-flip-enter-active,
.transition-flip-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-flip-enter-from {
  opacity: 0;
  transform: rotateY(-90deg);
}

.transition-flip-leave-to {
  opacity: 0;
  transform: rotateY(90deg);
}

/* 弹跳 */
.transition-bounce-enter-active {
  animation: bounce-in v-bind(duration + 'ms') v-bind(easing);
}

.transition-bounce-leave-active {
  animation: bounce-out v-bind(duration + 'ms') v-bind(easing);
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce-out {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  30% {
    transform: scale(1.05);
  }
  100% {
    opacity: 0;
    transform: scale(0.3);
  }
}

/* 弹性 */
.transition-elastic-enter-active {
  animation: elastic-in v-bind(duration + 'ms') ease-out;
}

.transition-elastic-leave-active {
  animation: elastic-out v-bind(duration + 'ms') ease-in;
}

@keyframes elastic-in {
  0% {
    opacity: 0;
    transform: scale(0) rotate(-360deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.2) rotate(-180deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

@keyframes elastic-out {
  0% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.2) rotate(180deg);
  }
  100% {
    opacity: 0;
    transform: scale(0) rotate(360deg);
  }
}

/* 旋转 */
.transition-rotate-enter-active,
.transition-rotate-leave-active {
  transition: all v-bind(duration + 'ms') v-bind(easing);
}

.transition-rotate-enter-from {
  opacity: 0;
  transform: rotate(-180deg) scale(0.5);
}

.transition-rotate-leave-to {
  opacity: 0;
  transform: rotate(180deg) scale(0.5);
}

/* 缓动函数映射 */
.transition-bounce-enter-active,
.transition-bounce-leave-active {
  transition-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.transition-elastic-enter-active,
.transition-elastic-leave-active {
  transition-timing-function: cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* 减少动画模式 */
@media (prefers-reduced-motion: reduce) {
  .transition-fade-enter-active,
  .transition-fade-leave-active,
  .transition-slide-up-enter-active,
  .transition-slide-up-leave-active,
  .transition-slide-down-enter-active,
  .transition-slide-down-leave-active,
  .transition-slide-left-enter-active,
  .transition-slide-left-leave-active,
  .transition-slide-right-enter-active,
  .transition-slide-right-leave-active,
  .transition-scale-enter-active,
  .transition-scale-leave-active,
  .transition-zoom-enter-active,
  .transition-zoom-leave-active,
  .transition-flip-enter-active,
  .transition-flip-leave-active,
  .transition-rotate-enter-active,
  .transition-rotate-leave-active {
    transition-duration: 0.01ms !important;
  }

  .transition-bounce-enter-active,
  .transition-bounce-leave-active,
  .transition-elastic-enter-active,
  .transition-elastic-leave-active {
    animation-duration: 0.01ms !important;
  }
}
</style>
