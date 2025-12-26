/**
 * Vue 3 组件类型声明
 * 支持 .vue 文件的 TypeScript 类型推导
 */

declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

/**
 * NativeScript Vue 3 全局类型增强
 */
declare module '@vue/runtime-core' {
  export interface ComponentCustomProperties {
    // 可以在这里添加全局属性类型
  }
}

