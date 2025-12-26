<template>
  <Page>
    <ActionBar title="环境测试" />
    <ScrollView>
      <StackLayout class="p-20">
        <Label 
          text="🎉 如果您看到这个界面" 
          class="text-3xl text-center m-b-10" 
          textWrap="true"
        />
        <Label 
          text="说明 NativeScript 环境完全正常！" 
          class="text-xl text-center m-b-30" 
          textWrap="true"
        />
        
        <StackLayout class="bg-blue-100 p-20 m-b-20" style="border-radius: 10;">
          <Label text="✅ Java 17 环境" class="text-lg font-bold m-b-5" />
          <Label text="OpenJDK 17.0.13" class="text-sm" />
        </StackLayout>
        
        <StackLayout class="bg-green-100 p-20 m-b-20" style="border-radius: 10;">
          <Label text="✅ NativeScript Runtime" class="text-lg font-bold m-b-5" />
          <Label text="Version 8.9.2" class="text-sm" />
        </StackLayout>
        
        <StackLayout class="bg-purple-100 p-20 m-b-20" style="border-radius: 10;">
          <Label text="✅ Vue 3 框架" class="text-lg font-bold m-b-5" />
          <Label text="Composition API" class="text-sm" />
        </StackLayout>
        
        <Button 
          text="点击测试交互" 
          @tap="onTest" 
          class="btn btn-primary m-t-20"
        />
        
        <Label 
          v-if="clicked"
          text="✅ 交互正常！" 
          class="text-center text-green-600 m-t-20 text-xl font-bold"
        />
        
        <Label 
          text="如果看到此页面，您可以：&#10;1. 返回修改原始代码&#10;2. 继续开发应用功能" 
          class="text-center text-gray-600 m-t-30 text-sm"
          textWrap="true"
        />
      </StackLayout>
    </ScrollView>
  </Page>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const clicked = ref(false);

function onTest() {
  clicked.value = true;
  console.log('✅ 按钮点击测试通过！');
}
</script>

<style scoped>
.bg-blue-100 {
  background-color: #E3F2FD;
}

.bg-green-100 {
  background-color: #E8F5E9;
}

.bg-purple-100 {
  background-color: #F3E5F5;
}

.text-gray-600 {
  color: #757575;
}

.text-green-600 {
  color: #43A047;
}

.font-bold {
  font-weight: bold;
}
</style>

