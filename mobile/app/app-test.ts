/**
 * 测试版本 - 验证环境是否正常
 * 如果能看到界面，说明 Java 17 和 NativeScript 环境完全正常
 */
import { createApp } from 'nativescript-vue';
import TestPage from './TestPage.vue';

// 引入样式
import './app.scss';

console.log('🚀 测试应用启动...');

// 创建应用
const app = createApp(TestPage);

// 启动应用
app.start();

console.log('✅ 应用已启动，如果看到测试界面，说明环境完全正常！');

