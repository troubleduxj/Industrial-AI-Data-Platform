<template>
  <div class="theme-compliance-dashboard">
    <div class="dashboard-header">
      <h2 class="dashboard-title">主题合规性监控</h2>
      <div class="dashboard-actions">
        <n-button
          type="primary"
          :loading="checking"
          class="standard-button"
          @click="checkCurrentPage"
        >
          检查当前页面
        </n-button>
        <n-button :loading="batchChecking" class="standard-button" @click="checkAllSystemPages">
          批量检查系统页面
        </n-button>
        <n-button :loading="refreshing" class="standard-button" @click="refreshDashboard">
          刷新
        </n-button>
      </div>
    </div>

    <!-- 合规性摘要 -->
    <div v-if="summary" class="compliance-summary">
      <div class="summary-cards">
        <div class="summary-card">
          <div v-if="summary.overallCompliance > 80" class="card-icon success">
            <TheIcon icon="checkmark-circle-outline" size="24" />
          </div>
          <div v-else-if="summary.overallCompliance > 60" class="card-icon warning">
            <TheIcon icon="warning-outline" size="24" />
          </div>
          <div v-else class="card-icon error">
            <TheIcon icon="close-circle-outline" size="24" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ summary.overallCompliance }}%</div>
            <div class="card-label">总体合规率</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon info">
            <TheIcon icon="document-text-outline" size="24" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ summary.totalReports }}</div>
            <div class="card-label">已检查页面</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon error">
            <TheIcon icon="warning-outline" size="24" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ summary.totalViolations }}</div>
            <div class="card-label">违规问题</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon success">
            <TheIcon icon="shield-outline" size="24" />
          </div>
          <div class="card-content">
            <div class="card-value">{{ summary.compliantPages }}</div>
            <div class="card-label">合规页面</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 违规统计图表 -->
    <div v-if="summary && summary.totalViolations > 0" class="violation-charts">
      <div class="chart-container">
        <h3>违规类型分布</h3>
        <div class="violation-types">
          <div
            v-for="(count, type) in summary.violationsByType"
            :key="type"
            class="violation-type-item"
          >
            <div class="type-label">{{ getViolationTypeLabel(type) }}</div>
            <div class="type-count">{{ count }}</div>
            <div class="type-bar">
              <div
                class="type-bar-fill"
                :style="{ width: (count / summary.totalViolations) * 100 + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-container">
        <h3>严重程度分布</h3>
        <div class="severity-distribution">
          <div class="severity-item high">
            <div class="severity-label">高</div>
            <div class="severity-count">{{ summary.violationsBySeverity.high }}</div>
          </div>
          <div class="severity-item medium">
            <div class="severity-label">中</div>
            <div class="severity-count">{{ summary.violationsBySeverity.medium }}</div>
          </div>
          <div class="severity-item low">
            <div class="severity-label">低</div>
            <div class="severity-count">{{ summary.violationsBySeverity.low }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细报告列表 -->
    <div class="reports-section">
      <h3>详细报告</h3>
      <div v-if="reports.length === 0" class="no-reports">
        <n-empty description="暂无检查报告">
          <template #extra>
            <n-button type="primary" class="standard-button" @click="checkCurrentPage">
              开始检查
            </n-button>
          </template>
        </n-empty>
      </div>

      <div v-else class="reports-list">
        <div
          v-for="report in reports"
          :key="report.pageId || report.timestamp"
          class="report-item"
          :class="{
            compliant: report.status === 'compliant',
            'non-compliant': report.status === 'non-compliant',
            error: report.status === 'error',
          }"
        >
          <div class="report-header">
            <div class="report-title">
              <TheIcon
                :icon="
                  report.status === 'compliant'
                    ? 'checkmark-circle-outline'
                    : report.status === 'non-compliant'
                    ? 'close-circle-outline'
                    : 'alert-circle-outline'
                "
                size="16"
                class="status-icon"
              />
              {{ getReportTitle(report) }}
            </div>
            <div class="report-meta">
              <span class="report-time">{{ formatTime(report.timestamp) }}</span>
              <n-button size="small" class="standard-button" @click="toggleReportDetails(report)">
                {{ expandedReports.has(report.pageId || report.timestamp) ? '收起' : '详情' }}
              </n-button>
            </div>
          </div>

          <div v-if="report.summary" class="report-summary">
            <span class="summary-item"> 总违规: {{ report.summary.totalViolations }} </span>
            <span v-if="report.summary.highSeverity > 0" class="summary-item high">
              高: {{ report.summary.highSeverity }}
            </span>
            <span v-if="report.summary.mediumSeverity > 0" class="summary-item medium">
              中: {{ report.summary.mediumSeverity }}
            </span>
            <span v-if="report.summary.lowSeverity > 0" class="summary-item low">
              低: {{ report.summary.lowSeverity }}
            </span>
          </div>

          <!-- 详细违规信息 -->
          <div v-if="expandedReports.has(report.pageId || report.timestamp)" class="report-details">
            <div v-if="report.violations && report.violations.length > 0">
              <h4>违规详情</h4>
              <div class="violations-list">
                <div
                  v-for="violation in report.violations"
                  :key="violation.id"
                  class="violation-item"
                  :class="violation.severity"
                >
                  <div class="violation-header">
                    <span class="violation-type">{{ getViolationTypeLabel(violation.type) }}</span>
                    <span class="violation-severity">{{
                      getSeverityLabel(violation.severity)
                    }}</span>
                  </div>
                  <div class="violation-message">{{ violation.message }}</div>
                  <div v-if="violation.element" class="violation-element">
                    元素: {{ violation.element }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="report.recommendations && report.recommendations.length > 0">
              <h4>修复建议</h4>
              <ul class="recommendations-list">
                <li v-for="(recommendation, index) in report.recommendations" :key="index">
                  {{ recommendation }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { NButton, NIcon, NEmpty } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
// 使用简单的图标替代，避免依赖问题
const CheckCircle = 'checkmark-circle-outline'
const XCircle = 'close-circle-outline'
const AlertCircle = 'alert-circle-outline'
const WarningCircle = 'warning-outline'
const AlertTriangle = 'warning-outline'
const FileText = 'document-text-outline'
const Shield = 'shield-outline'
import { useThemeStore } from '@/store/theme'

const themeStore = useThemeStore()

// 响应式数据
const checking = ref(false)
const batchChecking = ref(false)
const refreshing = ref(false)
const reports = ref([])
const summary = ref(null)
const expandedReports = ref(new Set())

// 计算属性
const sortedReports = computed(() => {
  return [...reports.value].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp)
  })
})

// 方法
const checkCurrentPage = async () => {
  checking.value = true
  try {
    const report = await themeStore.checkThemeCompliance()
    updateReports(report)
    await updateSummary()
  } catch (error) {
    console.error('检查当前页面失败:', error)
  } finally {
    checking.value = false
  }
}

const checkAllSystemPages = async () => {
  batchChecking.value = true
  try {
    const batchResult = await themeStore.checkSystemPagesCompliance()

    // 将批量结果转换为单个报告
    Object.entries(batchResult.results).forEach(([pageName, result]) => {
      if (result.found) {
        updateReports({
          ...result,
          pageId: pageName,
          pageName: pageName,
        })
      }
    })

    await updateSummary()
  } catch (error) {
    console.error('批量检查失败:', error)
  } finally {
    batchChecking.value = false
  }
}

const refreshDashboard = async () => {
  refreshing.value = true
  try {
    await updateSummary()
  } catch (error) {
    console.error('刷新失败:', error)
  } finally {
    refreshing.value = false
  }
}

const updateReports = (newReport) => {
  const existingIndex = reports.value.findIndex(
    (r) => (r.pageId || r.timestamp) === (newReport.pageId || newReport.timestamp)
  )

  if (existingIndex >= 0) {
    reports.value[existingIndex] = newReport
  } else {
    reports.value.unshift(newReport)
  }
}

const updateSummary = async () => {
  try {
    summary.value = await themeStore.getComplianceSummary()
  } catch (error) {
    console.error('更新摘要失败:', error)
  }
}

const toggleReportDetails = (report) => {
  const key = report.pageId || report.timestamp
  if (expandedReports.value.has(key)) {
    expandedReports.value.delete(key)
  } else {
    expandedReports.value.add(key)
  }
}

const getReportTitle = (report) => {
  if (report.pageName) {
    return report.pageName
  }
  if (report.pageId) {
    return report.pageId.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  }
  if (report.url) {
    return new URL(report.url).pathname
  }
  return '未知页面'
}

const getViolationTypeLabel = (type) => {
  const labels = {
    'hardcoded-color': '硬编码颜色',
    'missing-css-variable': '缺少CSS变量',
    'missing-css-class': '缺少CSS类',
    'missing-component-variable': '缺少组件变量',
    'excessive-inline-styles': '过多内联样式',
    'inline-theme-style': '内联主题样式',
  }
  return labels[type] || type
}

const getSeverityLabel = (severity) => {
  const labels = {
    high: '高',
    medium: '中',
    low: '低',
  }
  return labels[severity] || severity
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await updateSummary()
})
</script>

<style scoped lang="scss">
.theme-compliance-dashboard {
  padding: var(--spacing-lg);
  background: var(--background-color-light);
  min-height: 100vh;

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-color-light);

    .dashboard-title {
      font-size: var(--font-size-2xl);
      font-weight: var(--font-weight-bold);
      color: var(--text-color-primary);
      margin: 0;
    }

    .dashboard-actions {
      display: flex;
      gap: var(--spacing-sm);
    }
  }

  .compliance-summary {
    margin-bottom: var(--spacing-lg);

    .summary-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: var(--spacing-md);

      .summary-card {
        background: var(--background-color-base);
        border: 1px solid var(--border-color-light);
        border-radius: var(--border-radius-lg);
        padding: var(--spacing-lg);
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
        box-shadow: var(--shadow-sm);

        .card-icon {
          width: 48px;
          height: 48px;
          border-radius: var(--border-radius-full);
          display: flex;
          align-items: center;
          justify-content: center;

          &.success {
            background: rgba(82, 196, 26, 0.1);
            color: var(--success-color);
          }

          &.warning {
            background: rgba(250, 173, 20, 0.1);
            color: var(--warning-color);
          }

          &.error {
            background: rgba(255, 77, 79, 0.1);
            color: var(--error-color);
          }

          &.info {
            background: rgba(24, 144, 255, 0.1);
            color: var(--info-color);
          }
        }

        .card-content {
          .card-value {
            font-size: var(--font-size-2xl);
            font-weight: var(--font-weight-bold);
            color: var(--text-color-primary);
            line-height: 1;
          }

          .card-label {
            font-size: var(--font-size-sm);
            color: var(--text-color-secondary);
            margin-top: var(--spacing-xs);
          }
        }
      }
    }
  }

  .violation-charts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);

    .chart-container {
      background: var(--background-color-base);
      border: 1px solid var(--border-color-light);
      border-radius: var(--border-radius-lg);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-sm);

      h3 {
        margin: 0 0 var(--spacing-md) 0;
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        color: var(--text-color-primary);
      }

      .violation-types {
        .violation-type-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-sm);

          .type-label {
            flex: 0 0 120px;
            font-size: var(--font-size-sm);
            color: var(--text-color-primary);
          }

          .type-count {
            flex: 0 0 30px;
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
          }

          .type-bar {
            flex: 1;
            height: 8px;
            background: var(--background-color-light);
            border-radius: var(--border-radius-full);
            overflow: hidden;

            .type-bar-fill {
              height: 100%;
              background: var(--primary-color);
              transition: width var(--transition-normal);
            }
          }
        }
      }

      .severity-distribution {
        display: flex;
        gap: var(--spacing-md);

        .severity-item {
          flex: 1;
          text-align: center;
          padding: var(--spacing-md);
          border-radius: var(--border-radius-base);

          &.high {
            background: rgba(255, 77, 79, 0.1);
            color: var(--error-color);
          }

          &.medium {
            background: rgba(250, 173, 20, 0.1);
            color: var(--warning-color);
          }

          &.low {
            background: rgba(24, 144, 255, 0.1);
            color: var(--info-color);
          }

          .severity-label {
            font-size: var(--font-size-sm);
            margin-bottom: var(--spacing-xs);
          }

          .severity-count {
            font-size: var(--font-size-xl);
            font-weight: var(--font-weight-bold);
          }
        }
      }
    }
  }

  .reports-section {
    background: var(--background-color-base);
    border: 1px solid var(--border-color-light);
    border-radius: var(--border-radius-lg);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);

    h3 {
      margin: 0 0 var(--spacing-md) 0;
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-semibold);
      color: var(--text-color-primary);
    }

    .no-reports {
      text-align: center;
      padding: var(--spacing-xl);
    }

    .reports-list {
      .report-item {
        border: 1px solid var(--border-color-light);
        border-radius: var(--border-radius-base);
        margin-bottom: var(--spacing-md);
        overflow: hidden;

        &.compliant {
          border-left: 4px solid var(--success-color);
        }

        &.non-compliant {
          border-left: 4px solid var(--error-color);
        }

        &.error {
          border-left: 4px solid var(--warning-color);
        }

        .report-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-md);
          background: var(--background-color-light);

          .report-title {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);

            .status-icon {
              &.compliant {
                color: var(--success-color);
              }

              &.non-compliant {
                color: var(--error-color);
              }

              &.error {
                color: var(--warning-color);
              }
            }
          }

          .report-meta {
            display: flex;
            align-items: center;
            gap: var(--spacing-sm);

            .report-time {
              font-size: var(--font-size-sm);
              color: var(--text-color-secondary);
            }
          }
        }

        .report-summary {
          padding: var(--spacing-sm) var(--spacing-md);
          display: flex;
          gap: var(--spacing-md);
          background: var(--background-color-base);

          .summary-item {
            font-size: var(--font-size-sm);
            padding: 2px var(--spacing-xs);
            border-radius: var(--border-radius-sm);
            background: var(--background-color-light);

            &.high {
              background: rgba(255, 77, 79, 0.1);
              color: var(--error-color);
            }

            &.medium {
              background: rgba(250, 173, 20, 0.1);
              color: var(--warning-color);
            }

            &.low {
              background: rgba(24, 144, 255, 0.1);
              color: var(--info-color);
            }
          }
        }

        .report-details {
          padding: var(--spacing-md);
          border-top: 1px solid var(--border-color-light);

          h4 {
            margin: 0 0 var(--spacing-sm) 0;
            font-size: var(--font-size-base);
            font-weight: var(--font-weight-medium);
            color: var(--text-color-primary);
          }

          .violations-list {
            .violation-item {
              padding: var(--spacing-sm);
              margin-bottom: var(--spacing-sm);
              border-radius: var(--border-radius-base);
              border-left: 3px solid;

              &.high {
                background: rgba(255, 77, 79, 0.05);
                border-left-color: var(--error-color);
              }

              &.medium {
                background: rgba(250, 173, 20, 0.05);
                border-left-color: var(--warning-color);
              }

              &.low {
                background: rgba(24, 144, 255, 0.05);
                border-left-color: var(--info-color);
              }

              .violation-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--spacing-xs);

                .violation-type {
                  font-weight: var(--font-weight-medium);
                  color: var(--text-color-primary);
                }

                .violation-severity {
                  font-size: var(--font-size-xs);
                  padding: 2px var(--spacing-xs);
                  border-radius: var(--border-radius-sm);
                  background: var(--background-color-light);
                }
              }

              .violation-message {
                font-size: var(--font-size-sm);
                color: var(--text-color-secondary);
                margin-bottom: var(--spacing-xs);
              }

              .violation-element {
                font-size: var(--font-size-xs);
                color: var(--text-color-disabled);
                font-family: monospace;
              }
            }
          }

          .recommendations-list {
            margin: 0;
            padding-left: var(--spacing-lg);

            li {
              margin-bottom: var(--spacing-xs);
              font-size: var(--font-size-sm);
              color: var(--text-color-secondary);
            }
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .theme-compliance-dashboard {
    padding: var(--spacing-md);

    .dashboard-header {
      flex-direction: column;
      gap: var(--spacing-md);
      align-items: stretch;
    }

    .violation-charts {
      grid-template-columns: 1fr;
    }

    .severity-distribution {
      flex-direction: column;
    }
  }
}
</style>
