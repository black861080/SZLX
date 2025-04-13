<script setup>
import { ref, onMounted, computed, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft, ArrowRight, Edit, Check, Delete } from '@element-plus/icons-vue'
import MainLayouts from "../layouts/MainLayouts.vue"
import { usePlanStore } from '../stores/plan'
import { marked } from 'marked'
import axios from 'axios'
import { useUserStore } from '../stores/user'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import '../assets/markdown.css'  // 引入全局markdown样式

// 配置marked以支持数学公式
marked.setOptions({
  renderer: new marked.Renderer(),
  highlight: function(code, lang) {
    return code;
  },
  pedantic: false,
  gfm: true,
  breaks: true,
  sanitize: false,
  smartypants: false,
  xhtml: false
})

// 添加数学公式渲染函数
const renderMath = (text, displayMode = false) => {
  try {
    return katex.renderToString(text, {
      displayMode: displayMode,
      throwOnError: false
    })
  } catch (e) {
    console.error('数学公式渲染错误:', e)
    return text
  }
}

// 添加Markdown渲染函数
const renderMarkdown = (text) => {
  if (!text) return ''

  // 处理行内数学公式 \( ... \)
  text = text.replace(/\\\((.*?)\\\)/g, (match, formula) => {
    return renderMath(formula, false)
  })

  // 处理块级数学公式 \[ ... \]
  text = text.replace(/\\\[(.*?)\\\]/g, (match, formula) => {
    return renderMath(formula, true)
  })

  // 处理 $ $ 行内公式
  text = text.replace(/\$(.*?)\$/g, (match, formula) => {
    // 避免处理货币符号
    if (formula.match(/^\s*[\d.,]+\s*$/)) return match;
    return renderMath(formula, false);
  })

  // 处理 $$ $$ 块级公式
  text = text.replace(/\$\$(.*?)\$\$/g, (match, formula) => {
    return renderMath(formula, true);
  })

  // 渲染Markdown
  return marked(text)
}

const planStore = usePlanStore()
const plans = ref([])
const showAddDialog = ref(false)
const currentDate = ref(new Date())
const hoveredDate = ref(null)
const hoveredPlans = ref([])
const viewType = ref('month')
const showEditDialog = ref(false)
const editingPlan = ref(null)
const showAIAdviceDialog = ref(false)
const aiAdvice = ref('')
const isLoadingAdvice = ref(false)
const drawerVisible = ref(false)
const hasExistingAdvice = ref(false)
const loadingText = ref('')
const selectedPlanId = ref(null)
const taskFilter = ref('urgent') // 添加任务过滤器状态：'all', 'urgent', 'normal', 'overdue'

// 新计划表单数据
const newPlan = ref({
  todo: '',
  deadline: '',
  level: '非紧急'
})

// 使用computed替代原来的ref
const urgentPlans = computed(() => {
  if (!plans.value) return []
  return plans.value.filter(plan => plan.level === '紧急')
})

// 添加过滤后的计划列表
const filteredPlans = computed(() => {
  if (!plans.value) return []

  const now = new Date()

  switch (taskFilter.value) {
    case 'all':
      return plans.value
    case 'urgent':
      return plans.value.filter(plan =>
        plan.level === '紧急' && new Date(plan.deadline) >= now
      )
    case 'normal':
      return plans.value.filter(plan =>
        plan.level === '非紧急' && new Date(plan.deadline) >= now
      )
    case 'overdue':
      return plans.value.filter(plan => new Date(plan.deadline) < now)
    default:
      return plans.value
  }
})

const statistics = computed(() => {
  if (!plans.value) return { total_plans: 0, urgent_plans: 0, overdue_plans: 0 }

  const now = new Date()
  return {
    total_plans: plans.value.length,
    urgent_plans: plans.value.filter(plan => plan.level === '紧急').length,
    overdue_plans: plans.value.filter(plan => new Date(plan.deadline) < now).length
  }
})

// 获取所有计划
const fetchPlans = async () => {
  try {
    plans.value = await planStore.getPlans()
  } catch (error) {
    ElMessage.error('获取计划失败')
  }
}

// 添加新计划
const addPlan = async () => {
  try {
    // 处理时区问题
    const planData = {
      ...newPlan.value,
    }
    await planStore.createPlan(planData)
    ElMessage.success('计划创建成功')
    showAddDialog.value = false
    await planStore.fetchPlans() // 强制刷新存储的数据
    plans.value = planStore.plans
    newPlan.value = { todo: '', deadline: '', level: '非紧急' }
  } catch (error) {
    ElMessage.error('创建计划失败')
  }
}

// 获取某天的计划数量
const getDayPlans = (date) => {
  if (!plans.value) return []  // 添加空值检查
  return plans.value.filter(plan => {
    const planDate = new Date(plan.deadline)
    return planDate.toDateString() === date.toDateString()
  })
}

// 处理日期悬停
const handleDateHover = (date) => {
  hoveredDate.value = date
  hoveredPlans.value = getDayPlans(date)
}

// 添加获取月份日期的函数
const getDatesInMonth = (date) => {
  const year = date.getFullYear()
  const month = date.getMonth()

  // 获取当月第一天
  const firstDay = new Date(year, month, 1)
  // 获取当月最后一天
  const lastDay = new Date(year, month + 1, 0)

  // 获取第一天是星期几（0-6）
  const firstDayWeek = firstDay.getDay()

  // 计算日历开始日期（可能在上个月）
  const startDate = new Date(firstDay)
  startDate.setDate(1 - firstDayWeek)

  const dates = []
  // 生成6周的日期
  for (let i = 0; i < 42; i++) {
    const currentDate = new Date(startDate)
    currentDate.setDate(startDate.getDate() + i)
    dates.push(currentDate)
  }

  return dates
}

// 处理计划点击事件
const handlePlanClick = (plan, event) => {
  // 阻止事件冒泡，避免触发父元素的点击事件
  event.stopPropagation()

  // 如果点击的是当前选中的计划，则取消选中
  if (selectedPlanId.value === plan.plan_id) {
    selectedPlanId.value = null
  } else {
    // 否则选中当前点击的计划
    selectedPlanId.value = plan.plan_id
  }
}

// 处理全天计划点击事件，定位到对应时间段的计划
const handleAllDayPlanClick = (plan, event) => {
  // 阻止事件冒泡
  event.stopPropagation()

  // 获取计划的小时
  const planHour = new Date(plan.deadline).getHours()

  // 找到对应的时间格子并滚动到该位置
  setTimeout(() => {
    const hourElement = document.querySelector(`.hour-row:nth-child(${planHour + 1})`)
    if (hourElement) {
      hourElement.scrollIntoView({ behavior: 'smooth', block: 'center' })

      // 高亮显示该计划
      selectedPlanId.value = plan.plan_id
    }
  }, 100)
}

// 点击页面其他区域时，取消选中状态
const clearSelectedPlan = () => {
  selectedPlanId.value = null
}

// 格式化日期的函数
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 修改 changeDate 方法
const changeDate = (direction) => {
  const newDate = new Date(currentDate.value)
  if (viewType.value === 'month') {
    newDate.setMonth(newDate.getMonth() + direction)
  } else if (viewType.value === 'week') {
    newDate.setDate(newDate.getDate() + (direction * 7))
  } else if (viewType.value === 'day') {  // 添加日视图的日期切换
    newDate.setDate(newDate.getDate() + direction)
  }
  currentDate.value = newDate
  selectedPlanId.value = null // 清除选中状态
}

const goToToday = () => {
  currentDate.value = new Date()
  selectedPlanId.value = null // 清除选中状态
}

const updatePlan = async () => {
  try {
    if (!editingPlan.value) return

    const planData = {
      todo: editingPlan.value.todo,
      deadline: editingPlan.value.deadline,
      level: editingPlan.value.level
    }

    await planStore.updatePlan(editingPlan.value.plan_id, planData)
    ElMessage.success('计划更新成功')
    showEditDialog.value = false
    await fetchPlans()  // 刷新计划列表
  } catch (error) {
    ElMessage.error('更新计划失败')
  }
}

const deletePlan = async (planId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个计划吗？', '删除计划', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      customClass: 'custom-dialog',
      confirmButtonClass: 'confirm-button',
      cancelButtonClass: 'cancel-button',
      distinguishCancelAndClose: true,
      center: true
    })

    await planStore.deletePlan(planId)
    ElMessage.success('计划删除成功')
    await fetchPlans()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除计划失败')
    }
  }
}

const openEditDialog = (plan) => {
  editingPlan.value = {
    plan_id: plan.plan_id,
    todo: plan.todo,
    deadline: plan.deadline,
    level: plan.level
  }
  showEditDialog.value = true
}

const getAIAdvice = async () => {
  isLoadingAdvice.value = true
  aiAdvice.value = ''
  showAIAdviceDialog.value = true

  try {
    // 等待对话框显示并且DOM更新
    await nextTick()
    
    // 检查元素是否存在
    const contentElementSelector = '.ai-advice-dialog .markdown-content'
    let contentElement = document.querySelector(contentElementSelector)
    
    // 如果找不到元素，尝试再等待一次渲染
    if (!contentElement) {
      console.warn(`首次尝试未找到 ${contentElementSelector} 元素，等待再次更新`)
      await nextTick()
      contentElement = document.querySelector(contentElementSelector)
    }
    
    // 设置回调函数处理流式输出
    await planStore.getAIAdvice((text) => {
      aiAdvice.value = text
      
      // 每次收到新内容后尝试渲染
      const adviceElement = document.querySelector(contentElementSelector)
      if (adviceElement) {
        try {
          adviceElement.innerHTML = renderMarkdown(text)
          adviceElement.scrollTop = adviceElement.scrollHeight
        } catch (e) {
          console.error('渲染AI建议内容时出错:', e)
        }
      } else {
        console.warn(`无法找到 ${contentElementSelector} 元素来渲染内容`)
      }
    })
  } catch (error) {
    console.error('获取AI建议失败:', error)
    ElMessage.error(error.message || '获取AI建议失败')
  } finally {
    isLoadingAdvice.value = false
  }
}

const showAdviceDrawer = async () => {
  drawerVisible.value = true

  try {
    // 先等待抽屉打开，DOM更新
    await nextTick()
    
    const existingAdvice = await planStore.getExistingAdvice()
    if (existingAdvice) {
      hasExistingAdvice.value = true
      planStore.aiAdvice = existingAdvice.content
      
      // 再次等待DOM更新，确保markdown-content元素已创建
      await nextTick()
      
      // 尝试获取内容元素
      const adviceElement = document.querySelector('.markdown-content')
      if (adviceElement) {
        try {
          // 直接一次性渲染所有内容
          const renderedContent = renderMarkdown(existingAdvice.content)
          adviceElement.innerHTML = renderedContent
        } catch (e) {
          console.error('渲染现有建议失败:', e)
        }
      } else {
        console.warn('未找到.markdown-content元素，无法渲染内容')
      }
    } else {
      await generateNewAdvice()
    }
  } catch (error) {
    console.error('获取建议失败:', error)
    ElMessage.error('获取建议失败')
  }
}

const generateNewAdvice = async () => {
  loadingText.value = '正在生成AI建议...'
  isLoadingAdvice.value = true
  planStore.aiAdvice = ''
  
  try {
    // 等待DOM更新，确保元素已创建
    await nextTick()
    
    // 预先清除loading状态，以便显示内容区域
    loadingText.value = ''
    
    // 等待DOM更新，确保内容元素已创建
    await nextTick()
    
    // 寻找Markdown内容元素
    let contentElement = document.querySelector('.markdown-content')
    
    // 如果找不到元素，尝试多次查找
    if (!contentElement) {
      console.warn('首次尝试未找到.markdown-content元素，尝试再次查找')
      
      // 额外的等待以确保DOM已经更新
      await new Promise(resolve => setTimeout(resolve, 100))
      contentElement = document.querySelector('.markdown-content')
      
      if (!contentElement) {
        console.warn('第二次尝试未找到.markdown-content元素，将创建一个元素')
        // 如果仍然找不到，手动创建一个元素
        contentElement = document.createElement('div')
        contentElement.className = 'markdown-content'
        document.querySelector('.advice-content')?.appendChild(contentElement)
      }
    }

    const response = await fetch('http://localhost:5000/plan_service/plans/ai_advice', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useUserStore().accessToken}`,
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      credentials: 'include',
      mode: 'cors'
    })

    if (!response.ok) {
      if (response.status === 403) {
        ElMessage.error('Token余额不足，请充值后继续使用')
        return
      }
      throw new Error(`请求失败: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let currentText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break

          // 累积文本
          currentText += data
          
          // 更新store中的值
          planStore.aiAdvice = currentText
          
          // 重新获取元素（保证每次都能找到最新的元素）
          contentElement = document.querySelector('.markdown-content') || contentElement
          
          // 如果找到了元素，则渲染内容
          if (contentElement) {
            try {
              // 渲染当前累积的内容
              contentElement.innerHTML = renderMarkdown(currentText)
              contentElement.scrollTop = contentElement.scrollHeight
            } catch (renderError) {
              console.error('渲染Markdown内容时出错:', renderError)
            }
          } else {
            console.warn('无法找到.markdown-content元素，无法渲染内容')
          }
          
          // 延迟一小段时间以平滑显示
          await new Promise(resolve => setTimeout(resolve, 10))
        }
      }
    }

    // 流式响应完成后再次确保内容被正确渲染
    await nextTick()
    contentElement = document.querySelector('.markdown-content') || contentElement
    if (contentElement && planStore.aiAdvice) {
      contentElement.innerHTML = renderMarkdown(planStore.aiAdvice)
      contentElement.scrollTop = contentElement.scrollHeight
    }

    hasExistingAdvice.value = true
  } catch (error) {
    console.error('生成建议失败:', error)
    ElMessage.error(error.message || '生成建议失败')
  } finally {
    isLoadingAdvice.value = false
    loadingText.value = ''
  }
}

// 添加一个watch，监听planStore.aiAdvice的变化以确保内容始终能被正确渲染
watch(() => planStore.aiAdvice, (newAdvice) => {
  if (!newAdvice) return
  
  // 等待DOM更新
  nextTick(() => {
    const contentElement = document.querySelector('.markdown-content')
    if (contentElement) {
      try {
        contentElement.innerHTML = renderMarkdown(newAdvice)
        contentElement.scrollTop = contentElement.scrollHeight
      } catch (e) {
        console.error('监听渲染AI建议内容时出错:', e)
      }
    }
  })
}, { immediate: false })

// 监听抽屉可见性变化
watch(() => drawerVisible.value, (isVisible) => {
  if (isVisible && planStore.aiAdvice) {
    // 当抽屉打开且有建议内容时，确保内容被渲染
    nextTick(() => {
      const contentElement = document.querySelector('.markdown-content')
      if (contentElement) {
        try {
          contentElement.innerHTML = renderMarkdown(planStore.aiAdvice)
          contentElement.scrollTop = contentElement.scrollHeight
        } catch (e) {
          console.error('抽屉打开时渲染AI建议内容出错:', e)
        }
      }
    })
  }
})

const regenerateAdvice = () => {
  generateNewAdvice()
}

const formatAdvice = (advice) => {
  // 可以在这里添加格式化逻辑，比如将换行转换为 <br> 等
  return advice.replace(/\n/g, '<br>')
}

// 组件卸载时清理 EventSource
onUnmounted(() => {
  if (window.adviceEventSource) {
    window.adviceEventSource.close()
  }
})

onMounted(async () => {
  await fetchPlans() // 只需要获取一次plans数据
})

// 添加新的辅助函数
const formatWeekRange = (startDate, endDate) => {
  return `${startDate.getMonth() + 1}月 ${startDate.getDate()} – ${endDate.getDate()}, ${endDate.getFullYear()}`
}

const formatHour = (hour) => {
  return `${hour}:00`
}

// 添加 getWeekDates 计算属性
const getWeekDates = computed(() => {
  const curr = new Date(currentDate.value)
  const week = []

  // 设置到本周的周日
  curr.setDate(curr.getDate() - curr.getDay())

  // 获取一周的日期
  for (let i = 0; i < 7; i++) {
    const date = new Date(curr)
    date.setDate(curr.getDate() + i)
    week.push(date)
  }

  return week
})

const isToday = (date) => {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const isCurrentHour = (hour) => {
  const now = new Date()
  return now.getHours() === hour
}

const getDayPlanDetails = (date) => {
  if (!plans.value) return []
  return plans.value.filter(plan => {
    const planDate = new Date(plan.deadline)
    return planDate.toDateString() === date.toDateString()
  })
}

// 添加视图切换时清除选中状态的监听
const changeViewType = (type) => {
  viewType.value = type
  selectedPlanId.value = null // 清除选中状态
}
</script>

<template>
  <main-layouts>
    <div class="dashboard-container">
      <!-- 左侧组件部分 -->
      <div class="side-widgets">
        <!-- 计划统计组件 -->
        <div class="widget-card">
          <div class="widget-header">
            <h3>计划统计</h3>
          </div>
          <div class="widget-content">
            <div class="statistics-grid">
              <div class="stat-item">
                <div class="stat-value">{{ statistics.total_plans }}</div>
                <div class="stat-label">总计划数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value urgent">{{ statistics.urgent_plans }}</div>
                <div class="stat-label">紧急计划</div>
              </div>
              <div class="stat-item">
                <div class="stat-value overdue">{{ statistics.overdue_plans }}</div>
                <div class="stat-label">已过期</div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI建议组件 -->
        <div class="widget-card">
          <div class="widget-header">
            <h3>AI助手</h3>
          </div>
          <div class="widget-content">
            <el-button
                type="primary"
                @click="showAdviceDrawer"
                class="ai-advice-button">
              查看定制建议
            </el-button>
          </div>
        </div>

        <!-- 紧急任务组件 -->
        <div class="widget-card urgent-tasks">
          <div class="widget-header">
            <h3>
              {{ taskFilter === 'all' ? '全部任务' :
                 taskFilter === 'urgent' ? '紧急任务' :
                 taskFilter === 'normal' ? '非紧急任务' : '已过期任务' }}
            </h3>
            <div class="task-filter-buttons">
              <el-radio-group v-model="taskFilter" size="small">
                <el-radio-button label="all">全部</el-radio-button>
                <el-radio-button label="urgent">紧急</el-radio-button>
                <el-radio-button label="normal">非紧急</el-radio-button>
                <el-radio-button label="overdue">已过期</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div class="widget-content scrollable">
            <div v-if="filteredPlans.length" class="urgent-plans">
              <div v-for="plan in filteredPlans" :key="plan.plan_id" class="urgent-plan-item">
                <span :class="['level-dot', plan.level]"></span>
                <span class="plan-text">{{ plan.todo }}</span>
                <span class="plan-deadline" :class="{ 'overdue-text': new Date(plan.deadline) < new Date() }">
                  {{ formatDate(plan.deadline) }}
                </span>
                <el-button size="small" type="primary" circle @click="openEditDialog(plan)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" type="danger" circle @click="deletePlan(plan.plan_id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-empty v-else :description="`暂无${
              taskFilter === 'all' ? '任务' :
              taskFilter === 'urgent' ? '紧急任务' :
              taskFilter === 'normal' ? '非紧急任务' : '已过期任务'
            }`"></el-empty>
          </div>
        </div>

      </div>


      <!-- 右侧日历部分 -->
      <div class="calendar-container">
        <div class="header">
          <h2>我的计划</h2>
          <el-button
            type="primary"
            class="custom-add-button"
            @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            新增计划
          </el-button>
        </div>

        <div class="calendar-nav">
          <div class="nav-left">
            <el-button-group>
              <el-button
                type="primary"
                text
                @click="changeDate(-1)"
                :title="viewType === 'month' ? '上个月' : viewType === 'week' ? '上周' : '前一天'">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button
                type="primary"
                text
                @click="changeDate(1)"
                :title="viewType === 'month' ? '下个月' : viewType === 'week' ? '下周' : '后一天'">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-button-group>
            <el-button type="primary" text @click="goToToday">今天</el-button>
          </div>

          <h3>{{ viewType === 'month'
            ? currentDate.toLocaleString('zh-CN', { year: 'numeric', month: 'long' })
            : viewType === 'week'
            ? formatWeekRange(getWeekDates[0], getWeekDates[6])
            : currentDate.toLocaleString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }}</h3>

          <div class="view-options">
            <el-button-group>
              <el-button type="primary" :class="{ active: viewType === 'month' }" @click="changeViewType('month')">Month</el-button>
              <el-button type="primary" :class="{ active: viewType === 'week' }" @click="changeViewType('week')">Week</el-button>
              <el-button type="primary" :class="{ active: viewType === 'day' }" @click="changeViewType('day')">Day</el-button>
            </el-button-group>
          </div>
        </div>

        <!-- 日历主体 -->
        <!-- 月视图 -->
        <div v-if="viewType === 'month'" class="calendar-grid">
          <!-- 星期表头 -->
          <div v-for="day in ['周日', '周一', '周二', '周三', '周四', '周五', '周六']" :key="day" class="calendar-header">
            {{ day }}
          </div>

          <!-- 日期格子 -->
          <div v-for="date in getDatesInMonth(currentDate)"
               :key="date.toISOString()"
               class="calendar-cell"
               :class="{ 'today': isToday(date) }"
               @mouseenter="handleDateHover(date)"
               @mouseleave="hoveredDate = null">
            <span class="date-number">{{ date.getDate() }}</span>
            <div class="plan-count" v-if="getDayPlans(date).length">
              {{ getDayPlans(date).length }}个计划
            </div>

            <!-- 只在有计划且鼠标悬停时显示计划详情 -->
            <div v-if="hoveredDate?.toDateString() === date.toDateString() && hoveredPlans.length > 0"
                 class="plan-tooltip">
              <div v-for="plan in hoveredPlans"
                   :key="plan.plan_id"
                   class="plan-tooltip-item">
                <div class="plan-tooltip-content">
                  <span :class="['level-dot', plan.level]"></span>
                  <span class="plan-tooltip-text">{{ plan.todo }}</span>
                </div>
                <div class="plan-tooltip-actions">
                  <el-button
                    size="small"
                    type="primary"
                    circle
                    @click.stop="openEditDialog(plan)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    circle
                    @click.stop="deletePlan(plan.plan_id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 周视图 -->
        <div v-else-if="viewType === 'week'" class="week-view">
          <!-- 周视图表格 -->
          <div class="week-table">
            <!-- 表头 -->
            <div class="week-header">
              <div class="time-column-header"></div>
              <div v-for="date in getWeekDates"
                   :key="date.toISOString()"
                   class="day-header"
                   :class="{ 'today': isToday(date) }">
                <div class="day-name">{{ date.toLocaleString('zh-CN', { weekday: 'short' }) }}</div>
                <div class="day-date">{{ date.getDate() }}</div>
              </div>
            </div>

            <!-- 全天事件行 -->
            <div class="all-day-row">
              <div class="time-label">
                <span>全天</span>
                <el-tooltip content="点击计划可定位到对应时间段" placement="right">
                  <span class="info-icon">i</span>
                </el-tooltip>
              </div>
              <div v-for="date in getWeekDates"
                   :key="date.toISOString()"
                   class="day-cell"
                   @click="clearSelectedPlan">
                <template v-for="plan in getDayPlanDetails(date)" :key="plan.plan_id">
                  <div class="plan-item"
                       :class="[plan.level, { 'selected': selectedPlanId === plan.plan_id }]"
                       @click="handleAllDayPlanClick(plan, $event)">
                    <span class="plan-title">{{ plan.todo }}</span>
                  </div>
                </template>
              </div>
            </div>

            <!-- 时间格子 -->
            <div class="time-grid">
              <div v-for="hour in 24" :key="hour-1" class="hour-row">
                <div class="time-label">{{ formatHour(hour-1) }}</div>
                <div v-for="date in getWeekDates"
                     :key="date.toISOString()"
                     class="hour-cell"
                     :class="{ 'current-hour': isCurrentHour(hour-1) }"
                     @click="clearSelectedPlan">
                  <template v-for="plan in getDayPlanDetails(date)" :key="plan.plan_id">
                    <div v-if="new Date(plan.deadline).getHours() === (hour-1)"
                         class="plan-item"
                         :class="[plan.level, { 'selected': selectedPlanId === plan.plan_id }]"
                         @click="handlePlanClick(plan, $event)">
                      <span class="plan-time">
                        {{ new Date(plan.deadline).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
                      </span>
                      <span class="plan-title">{{ plan.todo }}</span>
                      <!-- 选中时显示的操作按钮 -->
                      <div v-if="selectedPlanId === plan.plan_id" class="plan-actions">
                        <el-button size="small" type="primary" circle @click.stop="openEditDialog(plan)">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                        <el-button size="small" type="danger" circle @click.stop="deletePlan(plan.plan_id)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 日视图 -->
        <div v-else-if="viewType === 'day'" class="day-view">
          <div class="day-table">
            <!-- 日期头部 -->
            <div class="day-header">
              <div class="time-column-header"></div>
              <div class="single-day-header" :class="{ 'today': isToday(currentDate) }">
                <div class="day-name">{{ currentDate.toLocaleString('zh-CN', { weekday: 'short' }) }}</div>
                <div class="day-date">{{ currentDate.getDate() }}</div>
              </div>
            </div>

            <!-- 全天事件行 -->
            <div class="all-day-row">
              <div class="time-label">
                <span>全天</span>
                <el-tooltip content="点击计划可定位到对应时间段" placement="right">
                  <span class="info-icon">i</span>
                </el-tooltip>
              </div>
              <div class="day-cell" @click="clearSelectedPlan">
                <template v-for="plan in getDayPlanDetails(currentDate)" :key="plan.plan_id">
                  <div class="plan-item"
                       :class="[plan.level, { 'selected': selectedPlanId === plan.plan_id }]"
                       @click="handleAllDayPlanClick(plan, $event)">
                    <span class="plan-title">{{ plan.todo }}</span>
                  </div>
                </template>
              </div>
            </div>

            <!-- 时间格子 -->
            <div class="time-grid">
              <div v-for="hour in 24" :key="hour-1" class="hour-row">
                <div class="time-label">{{ formatHour(hour-1) }}</div>
                <div class="hour-cell-container" @click="clearSelectedPlan">
                  <template v-for="plan in getDayPlanDetails(currentDate)" :key="plan.plan_id">
                    <div v-if="new Date(plan.deadline).getHours() === (hour-1)"
                         class="plan-item"
                         :class="[plan.level, { 'selected': selectedPlanId === plan.plan_id }]"
                         @click="handlePlanClick(plan, $event)">
                      <span class="plan-time">
                        {{ new Date(plan.deadline).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
                      </span>
                      <span class="plan-title">{{ plan.todo }}</span>
                      <!-- 选中时显示的操作按钮 -->
                      <div v-if="selectedPlanId === plan.plan_id" class="plan-actions">
                        <el-button size="small" type="primary" circle @click.stop="openEditDialog(plan)">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                        <el-button size="small" type="danger" circle @click.stop="deletePlan(plan.plan_id)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 添加计划弹窗 -->
        <el-dialog
          v-model="showAddDialog"
          title="添加新计划"
          width="400px"
          :close-on-click-modal="false"
          custom-class="custom-dialog">
          <el-form :model="newPlan" label-position="top">
            <el-form-item label="计划内容">
              <el-input
                v-model="newPlan.todo"
                placeholder="请输入计划内容"
                :input-style="{ borderRadius: '8px' }" />
            </el-form-item>
            <el-form-item label="截止时间">
              <el-date-picker
                v-model="newPlan.deadline"
                type="datetime"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :timezone="'Asia/Shanghai'"
                placeholder="选择截止时间"
                style="width: 100%"
                class="custom-date-picker"
              />
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="newPlan.level" style="width: 100%">
                <el-option label="紧急" value="紧急" />
                <el-option label="非紧急" value="非紧急" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button class="cancel-button" @click="showAddDialog = false">取消</el-button>
              <el-button class="confirm-button" @click="addPlan">确定</el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 编辑计划的对话框 -->
        <el-dialog
          v-model="showEditDialog"
          title="编辑计划"
          width="400px"
          :close-on-click-modal="false"
          custom-class="custom-dialog">
          <el-form v-if="editingPlan" :model="editingPlan" label-position="top">
            <el-form-item label="计划内容">
              <el-input
                v-model="editingPlan.todo"
                placeholder="请输入计划内容"
                :input-style="{ borderRadius: '8px' }" />
            </el-form-item>
            <el-form-item label="截止时间">
              <el-date-picker
                v-model="editingPlan.deadline"
                type="datetime"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :timezone="'Asia/Shanghai'"
                placeholder="选择截止时间"
                style="width: 100%"
                class="custom-date-picker"
              />
            </el-form-item>
            <el-form-item label="优先级">
              <el-select v-model="editingPlan.level" style="width: 100%">
                <el-option label="紧急" value="紧急" />
                <el-option label="非紧急" value="非紧急" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button class="cancel-button" @click="showEditDialog = false">取消</el-button>
              <el-button class="confirm-button" @click="updatePlan">确定</el-button>
            </div>
          </template>
        </el-dialog>

        <!-- AI建议弹窗 -->
        <el-dialog
          v-model="showAIAdviceDialog"
          title="AI定制化建议"
          width="600px"
          custom-class="custom-dialog ai-advice-dialog"
          :destroy-on-close="false"
          :append-to-body="true">
          <div class="ai-advice-content">
            <div v-if="isLoadingAdvice" class="loading-container">
              <el-loading-icon />
              <p>AI正在分析您的计划...</p>
            </div>
            <!-- 为内容预先创建容器元素 -->
            <div v-else class="markdown-content"></div>
          </div>
        </el-dialog>

        <el-drawer
          v-model="drawerVisible"
          title="AI定制化建议"
          size="30%"
          :destroy-on-close="false"
          :append-to-body="true"
        >
          <div class="advice-content">
            <div v-if="loadingText" class="loading-container">
              <el-loading-icon />
              <p>{{ loadingText }}</p>
            </div>
            <template v-else>
              <!-- 为内容预先创建容器元素 -->
              <div v-if="planStore.aiAdvice || true" class="markdown-content"></div>
              <el-button
                v-if="hasExistingAdvice"
                @click="regenerateAdvice"
                :loading="isLoadingAdvice"
                class="regenerate-button"
              >
                生成建议
              </el-button>
            </template>
          </div>
        </el-drawer>
      </div>
    </div>
  </main-layouts>
</template>

<style scoped>
.dashboard-container {
  display: flex;
  gap: 20px;  /* 减小间距 */
  padding: 40px;
  max-width: 1440px;  /* 增加最大宽度 */
  margin: 0 auto;
}

.side-widgets {
  width: 350px;  /* 减小侧边栏宽度 */
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0; /* 防止侧边栏被压缩 */
  height: calc(100vh - 120px); /* 设置高度与日历容器一致 */
}

.calendar-container {
  flex: 1;
  padding: 24px;  /* 增加内边距 */
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  min-height: calc(100vh - 120px);
  max-width: calc(100% - 370px); /* 确保日历容器不会过宽 */
  display: flex; /* 添加flex布局 */
  flex-direction: column; /* 设置为列方向 */
}

.header, .calendar-nav {
  flex-shrink: 0; /* 防止头部和导航栏被压缩 */
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.calendar-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 12px;
}

.nav-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-left .el-button {
  background-color: #EDE9FE !important; /* 修改为浅紫色背景 */
  border: none;
  border-radius: 8px;
  height: 32px;
  width: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B46C1 !important; /* 添加紫色图标颜色 */
}

.nav-left .el-button:hover {
  background-color: #DDD6FE !important; /* 更改悬停颜色为稍深的紫色 */
}

.nav-left .el-button-group {
  display: flex;
  gap: 8px;
}

.nav-left .el-button-group .el-button + .el-button {
  margin-left: 0;
}

.view-options {
  display: flex;
  align-items: center;
}

.view-options .el-button-group {
  border-radius: 8px;
  overflow: hidden;
}

.view-options .el-button {
  background-color: #f0f0ff;
  border: none;
  padding: 8px 16px;
  color: #666;
}

.view-options .el-button.active {
  background-color: #7950f2;
  color: white;
}

.el-button.el-button--primary.is-text {
  padding: 8px 12px;
  border-radius: 4px;
}

.el-button.el-button--primary.is-text:hover {
  background-color: #f0f0ff;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;  /* 增加格子间距 */
  background: #f5f7fa;
  padding: 2px;  /* 添加内边距使边框显示完整 */
  flex: 1; /* 让日历网格占据剩余空间 */
  min-height: 600px; /* 设置最小高度 */
}

.calendar-header {
  padding: 10px;
  text-align: center;
  background: white;
  font-weight: bold;
}

.calendar-cell {
  position: relative;
  min-height: 90px;  /* 减小单元格高度，使整体高度更合理 */
  padding: 12px;  /* 增加内边距 */
  background: white;
  border: 1px solid #ebeef5;
}

.date-number {
  font-size: 14px;
  color: #606266;
}

.plan-count {
  font-size: 12px;
  color: #6B46C1;  /* 改为紫色，与"今天"按钮颜色一致 */
  margin-top: 5px;
}

.plan-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 250px;
}

.plan-tooltip-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid #ebeef5;
}

.plan-tooltip-item:last-child {
  border-bottom: none;
}

.plan-tooltip-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.plan-tooltip-text {
  font-size: 14px;
  color: #303133;
}

.plan-tooltip-actions {
  display: flex;
  gap: 4px;
}

.plan-tooltip-actions .el-button {
  padding: 6px;
}

.level-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.level-dot.紧急 {
  background-color: #F56C6C;
}

.level-dot.非紧急 {
  background-color: #67C23A;
}

.widget-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.widget-header {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.widget-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.urgent-plans {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.urgent-plan-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.plan-text {
  flex: 1;
  font-size: 14px;
  margin-left: 8px;  /* 添加左边距 */
}

.plan-deadline {
  font-size: 12px;
  color: #909399;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  text-align: center;
}

.stat-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.stat-value.urgent {
  color: #F56C6C;
}

.stat-value.overdue {
  color: #606266;
}

.urgent-tasks {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.urgent-tasks .widget-content.scrollable {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 290px); /* 调整最大高度，使其与右侧组件保持一致 */
  min-height: 550px; /* 添加最小高度，确保下半段不为空 */
}

.plan-actions {
  position: absolute;
  top: -30px; /* 默认在计划项上方显示 */
  right: 0;
  display: flex;
  gap: 4px;
  background-color: white;
  padding: 4px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 20; /* 确保操作按钮在最上层 */
}

/* 为全天事件行中的计划项添加特殊处理 */
.all-day-row .plan-item .plan-actions {
  top: auto; /* 取消顶部定位 */
  bottom: -30px; /* 改为底部定位 */
}

.plan-actions .el-button {
  transform: scale(0.8); /* 稍微缩小按钮 */
}

/* 确保全天事件行中选中的计划项不会被遮挡 */
.all-day-row .plan-item.selected {
  z-index: 15; /* 提高z-index */
}

.custom-add-button {
  background: linear-gradient(to right,#6c5dd3, #8e6cff) !important;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.custom-add-button:hover {
  opacity: 0.9;
}

/* 对话框相关样式 */
:deep(.custom-dialog) {
  border-radius: 24px !important;  /* 增加圆角 */
  overflow: hidden;
  margin-top: 10vh !important;  /* 向下移动对话框位置 */
}

:deep(.custom-dialog .el-dialog__header) {
  margin: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.custom-dialog .el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

:deep(.custom-dialog .el-dialog__body) {
  padding: 24px;
}

:deep(.custom-dialog .el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button {
  background-color: #f5f7fa;
  border: none;
  color: #606266;
  padding: 8px 20px;
  border-radius: 8px;
}

.confirm-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  color: white;
  padding: 8px 20px;
  border-radius: 8px;
}

:deep(.el-form-item__label) {
  padding-bottom: 8px;
  font-weight: 500;
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper),
:deep(.el-date-editor.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6;
}

:deep(.el-input__wrapper:hover),
:deep(.el-select .el-input__wrapper:hover),
:deep(.el-date-editor.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #6c5dd3;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-select .el-input__wrapper.is-focus),
:deep(.el-date-editor.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6c5dd3 !important;
}

/* 修改删除确认弹窗的按钮样式 */
:deep(.el-message-box.custom-dialog .el-message-box__btns .el-button--primary) {
  background: linear-gradient(to right, #6c5dd3, #8e6cff) !important;
  border: none;
  color: white;
  padding: 8px 20px;
  border-radius: 8px;
}

:deep(.el-message-box.custom-dialog .el-message-box__btns .el-button--default) {
  background-color: #f5f7fa !important;
  border: none;
  color: #606266;
  padding: 8px 20px;
  border-radius: 8px;
}

:deep(.el-message-box.custom-dialog .el-message-box__btns .el-button) {
  padding: 8px 20px;
  border-radius: 8px;
  margin-left: 12px;
}

:deep(.el-message-box.custom-dialog .el-message-box__btns .el-button:hover) {
  opacity: 0.9;
}

.ai-advice-button {
  width: 100%;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  height: 40px;
  border-radius: 8px;
}

.ai-advice-content {
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
  border-radius: 8px;
  background-color: #fafafa;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 16px;
}

.regenerate-button {
  margin-top: 20px;
  width: 100%;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  color: white;
  height: 40px;
  border-radius: 8px;
}

/* 添加数学公式相关样式 */
:deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 1em 0;
  margin: 0.5em 0;
}

:deep(.katex) {
  font-size: 1.1em;
  line-height: 1.2;
  white-space: normal;
}

:deep(.katex-html) {
  white-space: normal;
}

/* 添加Markdown内容样式 */
:deep(.markdown-content) {
  line-height: 1.6;
  padding: 16px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background-color: #f9f9f9;
  border-radius: 8px;
  min-height: 200px;
  max-height: 60vh;
}

.ai-advice-content {
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;
}

.advice-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
}

/* 周视图样式 */
.week-view {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  height: auto; /* 改为自动高度 */
  min-height: 750px; /* 添加最小高度，确保与月视图一致 */
  display: flex;
  flex-direction: column;
  width: 100%; /* 确保周视图占满容器宽度 */
  flex: 1; /* 占据剩余空间 */
}

.week-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%; /* 确保表格占满容器宽度 */
}

.week-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #ebeef5;
  width: 100%; /* 确保表头占满容器宽度 */
}

.time-column-header,
.day-header {
  padding: 8px;
  text-align: center;
  border-right: 1px solid #ebeef5;
}

.day-name {
  font-size: 14px;
  color: #606266;
}

.day-date {
  font-size: 16px;
  font-weight: 500;
  margin-top: 4px;
}

.all-day-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #ebeef5;
  min-height: 48px;
  max-height: 120px;
  padding: 4px 0;
  margin-bottom: 30px; /* 添加底部边距，为操作按钮留出空间 */
  position: relative; /* 添加相对定位 */
  z-index: 2; /* 确保全天事件行在时间格子之上 */
}

.all-day-row .day-cell {
  padding: 2px;
  border-right: 1px solid #ebeef5;
  overflow-y: auto;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
  position: relative; /* 添加相对定位 */
  padding-bottom: 30px; /* 为操作按钮预留空间 */
}

.all-day-row .plan-item {
  margin: 2px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 24px; /* 添加固定高度 */
  line-height: 16px; /* 添加固定行高 */
  box-sizing: border-box; /* 确保padding不会增加元素总高度 */
  display: flex; /* 使用flex布局替代inline-block */
  align-items: center; /* 垂直居中内容 */
  cursor: pointer; /* 添加指针样式 */
}

.all-day-row .plan-item:hover {
  background-color: rgba(108, 93, 211, 0.1); /* 添加悬停背景色 */
  transform: translateY(-1px); /* 轻微上移 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 添加阴影 */
}

.time-grid {
  flex: 1;
  overflow-y: auto;
  margin-top: -20px; /* 向上移动时间格子，减少全天事件行留下的空白 */
  min-height: 570px; /* 设置最小高度，确保与月视图一致 */
  max-height: 570px; /* 设置最大高度，确保所有视图一致 */
}

.hour-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  min-height: 48px;
  border-bottom: 1px solid #ebeef5;
}

.time-label {
  padding: 8px;
  color: #909399;
  font-size: 12px;
  text-align: right;
  border-right: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: #909399;
  color: white;
  font-size: 10px;
  font-style: italic;
  cursor: help;
}

.hour-cell {
  border-right: 1px solid #ebeef5;
  padding: 2px;
  position: relative;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 4px;
}

.plan-item {
  margin: 2px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  width: auto; /* 允许计划项目自适应宽度 */
  max-width: 100%; /* 限制最大宽度 */
  display: flex; /* 改为flex布局 */
  align-items: center; /* 垂直居中 */
  height: 24px; /* 固定高度 */
  line-height: 16px; /* 固定行高 */
  box-sizing: border-box; /* 确保padding不会增加元素总高度 */
  position: relative; /* 添加相对定位，用于定位操作按钮 */
}

.plan-item.selected {
  z-index: 10; /* 确保选中的计划项在最上层 */
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2); /* 添加阴影效果 */
  transform: scale(1.05); /* 稍微放大 */
}

.plan-item.紧急 {
  background-color: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.plan-item.非紧急 {
  background-color: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.plan-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.current-hour {
  background-color: rgba(108, 93, 211, 0.05);
}

.today {
  background-color: #f0f2ff;
}

.plan-time {
  color: #909399;
  margin-right: 8px;
}

.plan-title {
  color: #303133;
  font-weight: 500;
}

.calendar-cell.today {
  background-color: #f0f2ff;  /* 浅紫色背景 */
  border: 1px solid #6c5dd3;  /* 紫色边框 */
}

.calendar-cell.today .date-number {
  color: #6c5dd3;  /* 紫色日期文字 */
  font-weight: 600;
}

/* 日视图样式 */
.day-view {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  height: auto; /* 改为自动高度 */
  min-height: 750px; /* 添加最小高度，确保与月视图一致 */
  display: flex;
  flex-direction: column;
  width: 100%; /* 确保日视图占满容器宽度 */
  flex: 1; /* 占据剩余空间 */
}

.day-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%; /* 确保表格占满容器宽度 */
}

.day-header {
  display: grid;
  grid-template-columns: 80px 1fr;
  border-bottom: 1px solid #ebeef5;
}

.single-day-header {
  padding: 8px;
  text-align: center;
  border-right: 1px solid #ebeef5;
}

.single-day-header.today {
  background-color: #f0f2ff;
}

/* 日视图的全天事件行样式 */
.day-view .all-day-row {
  display: flex;
  width: 100%;
  border-bottom: 1px solid #ebeef5;
  min-height: 48px;
  margin-bottom: 30px; /* 添加底部边距 */
}

.day-view .all-day-row .day-cell {
  flex: 1;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  padding-bottom: 30px; /* 为操作按钮预留空间 */
}

.day-view .time-grid {
  margin-top: -20px; /* 向上移动时间格子，减少全天事件行留下的空白 */
}

/* 日视图样式修改 - 完全重写 */
.day-view .hour-row {
  display: flex;
  width: 100%;
  min-height: 48px;
  border-bottom: 1px solid #ebeef5;
}

.day-view .time-label {
  width: 80px;
  flex-shrink: 0;
  padding: 8px;
  color: #909399;
  font-size: 12px;
  text-align: right;
  border-right: 1px solid #ebeef5;
}

.day-view .hour-cell-container {
  flex: 1;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  min-height: 48px;
}

.day-view .plan-item {
  display: inline-flex;
  align-items: center;
  margin: 2px;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  max-width: fit-content;
}

/* 日视图的全天事件行样式 */
.day-view .all-day-row {
  display: flex;
  width: 100%;
  border-bottom: 1px solid #ebeef5;
  min-height: 48px;
  margin-bottom: 30px; /* 添加底部边距 */
}

.day-view .all-day-row .time-label {
  width: 80px;
  flex-shrink: 0;
  padding: 8px;
  color: #909399;
  font-size: 12px;
  text-align: right;
  border-right: 1px solid #ebeef5;
}

.day-view .all-day-row .day-cell {
  flex: 1;
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  padding-bottom: 30px; /* 为操作按钮预留空间 */
}

.day-view .time-grid {
  margin-top: -20px; /* 向上移动时间格子，减少全天事件行留下的空白 */
}

/* 修改任务过滤器样式 */
.task-filter-buttons {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.task-filter-buttons :deep(.el-radio-group) {
  display: flex;
  gap: 8px;
  width: 100%;
}

.task-filter-buttons :deep(.el-radio-button) {
  flex: 1;
}

.task-filter-buttons :deep(.el-radio-button__inner) {
  width: 100%;
  padding: 8px 0;
  font-size: 13px;
  border: 1px solid #e4e7ed;
  border-radius: 8px !important;
  transition: all 0.3s;
  background-color: #fff;
  color: #606266;
  box-shadow: none !important;
}

/* 移除默认边框样式 */
.task-filter-buttons :deep(.el-radio-button:not(:last-child)) {
  margin-right: 0;
}

.task-filter-buttons :deep(.el-radio-button:not(:last-child) .el-radio-button__inner) {
  border-right: 1px solid #e4e7ed;
}

/* 选中状态样式 */
.task-filter-buttons :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(to right, #6c5dd3, #8e6cff) !important;
  border-color: transparent !important;
  color: white !important;
  box-shadow: none !important;
}

/* 悬停状态样式 */
.task-filter-buttons :deep(.el-radio-button__inner:hover) {
  background-color: #f5f7fa;
  border-color: #6c5dd3;
  color: #6c5dd3;
}

.task-filter-buttons :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner:hover) {
  background: linear-gradient(to right, #6c5dd3, #8e6cff) !important;
  opacity: 0.9;
  color: white !important;
}

/* 移除默认的连接样式 */
.task-filter-buttons :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px !important;
}

.task-filter-buttons :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 8px !important;
}

.overdue-text {
  color: #F56C6C !important;
  font-weight: 500;
}

.level-dot.非紧急 {
  background-color: #67C23A;
}

.day-view .all-day-row .time-label {
  width: 80px;
  flex-shrink: 0;
  padding: 8px;
  color: #909399;
  font-size: 12px;
  text-align: right;
  border-right: 1px solid #ebeef5;
}
</style>

