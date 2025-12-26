/**
 * DeviceMonitor Mobile App
 * NativeScript-Vue 3 + TypeScript
 */
import { createApp } from 'nativescript-vue';
import { createPinia } from 'pinia';
import LoginPage from './pages/LoginPage.vue';

// 引入样式
import './app.scss';

// 创建 Pinia 实例
const pinia = createPinia();

// 创建 Vue 应用
const app = createApp(LoginPage);

// 注册 Pinia
app.use(pinia);

// 启动应用
app.start();
