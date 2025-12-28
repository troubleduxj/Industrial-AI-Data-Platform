<template>
  <div class="migration-status-page">
    <n-grid :cols="24" :x-gap="16" :y-gap="16">
      <!-- 迁移状态概览 -->
      <n-gi :span="24">
        <n-card title="迁移状态概览" size="small">
          <n-grid :cols="4" :x-gap="16">
            <n-gi>
              <n-statistic label="当前架构" :value="status.current_architecture">
                <template #prefix>
                  <n-icon :color="status.current_architecture === 'new' ? '#18a058' : '#f0a020'">
                    <ServerOutline />
                  </n-icon>
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="迁移进度" :value="status.progress + '%'">
                <template #suffix>
                  <n-progress type="circle" :percentage="status.progress" :stroke-width="4" style="width: 40px;" />
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="已迁移记录" :value="status.migrated_count" />
            </n-gi>
            <n-gi>
              <n-statistic label="待迁移记录" :value="status.pending_count" />
            </n-gi>
          </n-grid>
        </n-card>
      </n-gi>

      <!-- 迁移操作 -->
      <n-gi :span="12">
        <n-card title="迁移操作" size="small">
          <n-space vertical>
            <n-alert v-if="status.current_architecture === 'old'" type="info" title="提示">
              当前系统运行在旧架构上，可以执行数据迁移切换到新架构。
            </n-alert>
            <n-alert v-else type="success" title="提示">
              系统已切换到新架构，如需回滚请谨慎操作。
            </n-alert>

            <n-space>
              <n-button type="primary" @click="handleMigrate" :loading="migrating" :disabled="status.current_architecture === 'new'">
                执行迁移
              </n-button>
              <n-button type="info" @click="handleValidate" :loading="validating">
                验证数据
              </n-button>
              <n-button type="warning" @click="handleSwitch" :loading="switching">
                切换架构
              </n-button>
              <n-button type="error" @click="handleRollback" :loading="rollingBack" :disabled="status.current_architecture === 'old'">
                回滚
              </n-button>
            </n-space>
          </n-space>
        </n-card>
      </n-gi>

      <!-- 数据对比 -->
      <n-gi :span="12">
        <n-card title="数据对比" size="small">
          <n-data-table :columns="comparisonColumns" :data="comparison" size="small" />
        </n-card>
      </n-gi>

      <!-- 迁移日志 -->
      <n-gi :span="24">
        <n-card title="迁移日志" size="small">
          <template #header-extra>
            <n-button size="small" @click="loadLogs">刷新</n-button>
          </template>
          <n-log :log="logs" :rows="15" language="log" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, h } from 'vue'
import { NTag, useMessage, useDialog } from 'naive-ui'
import { ServerOutline } from '@vicons/ionicons5'
import { platformApi } from '@/api/v3/platform'

const message = useMessage()
const dialog = useDialog()

const migrating = ref(false)
const validating = ref(false)
const switching = ref(false)
const rollingBack = ref(false)

const status = reactive({
  current_architecture: 'old',
  progress: 0,
  migrated_count: 0,
  pending_count: 0
})

const comparison = ref([])
const logs = ref('')

const comparisonColumns = [
  { title: '数据类型', key: 'type' },
  { title: '旧系统', key: 'old_count' },
  { title: '新系统', key: 'new_count' },
  {
    title: '状态',
    key: 'status',
    render: row => {
      const match = row.old_count === row.new_count
      return h(NTag, { type: match ? 'success' : 'warning' }, () => match ? '一致' : '不一致')
    }
  }
]

const loadStatus = async () => {
  try {
    const res = await platformApi.getMigrationStatus()
    Object.assign(status, res.data || {})
  } catch (error) {
    console.error('加载状态失败:', error)
  }
}

const loadComparison = async () => {
  try {
    const res = await platformApi.getDataComparison()
    comparison.value = res.data || []
  } catch (error) {
    console.error('加载对比数据失败:', error)
  }
}

const loadLogs = async () => {
  try {
    const res = await platformApi.getMigrationLogs()
    logs.value = res.data?.logs || '暂无日志'
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

const handleMigrate = () => {
  dialog.warning({
    title: '确认执行迁移',
    content: '确定要执行数据迁移吗？建议先在测试环境验证。',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      migrating.value = true
      try {
        await platformApi.executeMigration({ dry_run: false })
        message.success('迁移任务已启动')
        loadStatus()
        loadLogs()
      } catch (error) {
        message.error(error.message || '迁移失败')
      } finally {
        migrating.value = false
      }
    }
  })
}

const handleValidate = async () => {
  validating.value = true
  try {
    const res = await platformApi.validateMigration()
    if (res.data?.valid) {
      message.success('数据验证通过')
    } else {
      message.warning(`发现 ${res.data?.issues?.length || 0} 个问题`)
    }
    loadLogs()
  } catch (error) {
    message.error('验证失败')
  } finally {
    validating.value = false
  }
}

const handleSwitch = () => {
  const targetArch = status.current_architecture === 'old' ? '新' : '旧'
  dialog.warning({
    title: '确认切换架构',
    content: `确定要切换到${targetArch}架构吗？`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      switching.value = true
      try {
        const target = status.current_architecture === 'old' ? 'new' : 'old'
        await platformApi.switchArchitecture({ target })
        message.success('架构切换成功')
        loadStatus()
        loadLogs()
      } catch (error) {
        message.error(error.message || '切换失败')
      } finally {
        switching.value = false
      }
    }
  })
}

const handleRollback = () => {
  dialog.error({
    title: '确认回滚',
    content: '回滚将恢复到旧架构，确定要继续吗？',
    positiveText: '确定回滚',
    negativeText: '取消',
    onPositiveClick: async () => {
      rollingBack.value = true
      try {
        await platformApi.rollbackMigration()
        message.success('回滚成功')
        loadStatus()
        loadLogs()
      } catch (error) {
        message.error(error.message || '回滚失败')
      } finally {
        rollingBack.value = false
      }
    }
  })
}

onMounted(() => {
  loadStatus()
  loadComparison()
  loadLogs()
})
</script>

<style scoped>
.migration-status-page {
  padding: 16px;
}
</style>
