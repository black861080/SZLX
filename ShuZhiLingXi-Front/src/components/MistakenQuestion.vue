<template>
  <main-layouts>
    <div class="dashboard-container">
      <!-- 左侧边栏 -->
      <div class="side-widgets">
        <!-- 错题统计卡片 -->
        <div class="widget-card stats-card">
          <div class="stats-header">
            <h3>错题概览</h3>
          </div>
          <div class="statistics-grid">
            <div class="stat-item total">
              <div class="stat-value">{{ questionStore.statistics.total_count }}</div>
              <div class="stat-label">总错题</div>
            </div>
            <div class="stat-item image">
              <div class="stat-value">{{ questionStore.statistics.image_count }}</div>
              <div class="stat-label">图片题</div>
            </div>
            <div class="stat-item text">
              <div class="stat-value">{{ questionStore.statistics.favorite_count }}</div>
              <div class="stat-label">收藏</div>
            </div>
          </div>
        </div>

        <!-- 错题集列表卡片 -->
        <div class="widget-card list-card">
          <div class="widget-header">
            <h3>错题集</h3>
            <el-button
                type="primary"
                class="create-list-btn"
                @click="showCreateListDialog">
              <el-icon><Plus /></el-icon>
              新建错题集
            </el-button>
          </div>

          <!-- 错题集列表 -->
          <div class="list-container">
            <el-scrollbar>
              <el-collapse v-model="activeList">
                <el-collapse-item
                    v-for="list in questionStore.lists"
                    :key="list.question_list_id"
                    :name="list.question_list_id">
                  <template #title>
                    <div class="list-title">
                      <div class="list-title-content">
                        <span class="list-name">{{ list.name }}</span>
                        <el-tag
                            size="small"
                            type="info"
                            effect="plain"
                            class="question-count">
                          {{ list.count || 0 }} 题
                        </el-tag>
                      </div>
                      <el-button
                          type="primary"
                          size="small"
                          @click.stop="handleListSelect(list)"
                          class="view-btn">
                        <el-icon><View /></el-icon>
                        查看错题
                      </el-button>
                    </div>
                  </template>
                  <div class="list-content">
                    <div class="list-actions">
                      <div class="action-left">
                        <el-button
                            type="warning"
                            link
                            @click.stop="editList(list)"
                            class="edit-btn">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-button>
                      </div>
                      <div class="action-right">
                        <el-button
                            type="danger"
                            link
                            class="delete-btn"
                            @click.stop="deleteList(list.question_list_id)">
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-button>
                      </div>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </el-scrollbar>
          </div>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="questions-content">
        <div class="content-header">
          <h2>{{ questionStore.currentList?.name || '请选择错题集' }}</h2>
          <div class="header-actions">
            <el-button
                type="default"
                :class="{ 'is-active': showOnlyFavorites }"
                @click="toggleShowOnlyFavorites"
                :disabled="!questionStore.currentList">
              <el-icon><StarFilled /></el-icon>
              只看收藏
            </el-button>
            <el-button
                type="primary"
                @click="showCreateQuestionDialog"
                :disabled="!questionStore.currentList">
              <el-icon><Plus /></el-icon>
              添加错题
            </el-button>
          </div>
        </div>

        <!-- 错题列表 -->
        <el-scrollbar class="questions-scrollbar">
          <div class="questions-grid">
            <el-empty v-if="!questionStore.questions.length"
                      description="暂无错题"
                      class="custom-empty">
              <template #image>
                <div class="empty-image-wrapper">
                  <el-icon class="empty-icon"><Document /></el-icon>
                </div>
              </template>
              <template #description>
                <p class="empty-description">暂无错题，点击"添加错题"开始使用</p>
              </template>
            </el-empty>
            <el-card v-else
                     v-for="question in filteredQuestions"
                     :key="question.question_id"
                     class="question-card">
              <template #header>
                <div class="question-header">
                  <div class="question-info">
                    <span class="question-date">{{ formatDate(question.created_at) }}</span>
                  </div>
                  <div class="question-actions">
                    <el-button-group class="action-buttons">
                      <el-button
                          type="default"
                          size="small"
                          @click="toggleFavorite(question)"
                          class="favorite-btn"
                          :class="{ 'is-favorite': question.is_favorite }">
                        <el-icon>
                          <Star v-if="!question.is_favorite" />
                          <StarFilled v-else />
                        </el-icon>
                      </el-button>
                      <el-button
                          type="default"
                          size="small"
                          @click="editQuestion(question)"
                          class="edit-btn">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-button>
                      <el-button
                          type="danger"
                          size="small"
                          class="delete-btn"
                          @click="deleteQuestion(question.question_id)">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>
              <div class="question-content">
                <div class="text-section">
                  <div class="section-label">题目内容</div>
                  <div class="content-text" v-html="renderContent(question.content)"></div>
                </div>
                <div v-if="question.is_image" class="image-section">
                  <el-image
                      :src="question.image_url"
                      fit="contain"
                      class="question-image"
                      :preview-src-list="[question.image_url]"
                      :initial-index="0"
                      :hide-on-click-modal="false"
                      :zoom-rate="1.2"
                      :preview-teleported="true">
                    <template #error>
                      <div class="image-error">
                        <el-icon><Picture /></el-icon>
                        <span>图片加载失败</span>
                      </div>
                    </template>
                  </el-image>
                </div>
              </div>

              <!-- 答案部分 -->
              <div class="section">
                <div class="section-header" @click="toggleAnswer(question)">
                  <span class="section-title"><i class="el-icon-question"></i>答案解析</span>
                  <el-button
                      type="primary"
                      size="small"
                      :loading="question.generatingAnswer"
                      @click.stop="generateAnswer(question)"
                  >
                    <i class="el-icon-refresh"></i>
                    重新生成
                  </el-button>
                </div>
                <div v-show="question.showAnswer" class="section-content">
                  <div v-if="question.answer" class="content-text" v-html="renderContent(question.answer)"></div>
                  <div v-else class="empty-text">暂无答案，点击"重新生成"生成答案</div>
                </div>
              </div>

              <!-- 相似题目部分 -->
              <div class="section">
                <div class="section-header" @click="toggleSimilar(question)">
                  <span class="section-title"><i class="el-icon-connection"></i>相似题目</span>
                  <el-button
                      type="primary"
                      size="small"
                      :loading="question.generatingSimilar"
                      @click.stop="generateSimilar(question)"
                  >
                    <i class="el-icon-refresh"></i>
                    重新生成
                  </el-button>
                </div>
                <div v-show="question.showSimilar" class="section-content">
                  <div v-if="question.similar_question" class="content-text" v-html="renderContent(question.similar_question)"></div>
                  <div v-else class="empty-text">暂无相似题目，点击"重新生成"生成相似题目</div>
                </div>
              </div>

              <!-- 相似题目答案部分 -->
              <div class="section">
                <div class="section-header" @click="toggleSimilarAnswer(question)">
                  <span class="section-title"><i class="el-icon-data-analysis"></i>相似题目答案</span>
                  <el-button
                      type="primary"
                      size="small"
                      :loading="question.generatingSimilarAnswer"
                      @click.stop="generateSimilarAnswer(question)"
                  >
                    <i class="el-icon-refresh"></i>
                    重新生成
                  </el-button>
                </div>
                <div v-show="question.showSimilarAnswer" class="section-content">
                  <div v-if="question.similar_answer" class="content-text" v-html="renderContent(question.similar_answer)"></div>
                  <div v-else class="empty-text">暂无相似题目答案，点击"重新生成"生成答案</div>
                </div>
              </div>
            </el-card>
          </div>
        </el-scrollbar>
      </div>
    </div>

    <!-- 创建错题集对话框 -->
    <el-dialog
        v-model="listDialogVisible"
        :title="editingList ? '编辑错题集' : '新建错题集'"
        width="400px"
        :close-on-click-modal="false"
        :show-close="true">
      <el-form :model="listForm" label-width="80px" :rules="listRules" ref="listFormRef">
        <el-form-item label="名称" prop="name">
          <el-input
              v-model="listForm.name"
              placeholder="请输入错题集名称"
              maxlength="50"
              show-word-limit/>
          <div class="form-tip">给错题集起一个容易记住的名字</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="listDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleListSubmit" :loading="submitting">
            {{ editingList ? '保存修改' : '创建错题集' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建错题对话框 -->
    <el-dialog
        v-model="questionDialogVisible"
        :title="editingQuestion ? '编辑错题' : '新建错题'"
        width="600px"
        :close-on-click-modal="false"
        :show-close="true">
      <el-form :model="questionForm" label-width="80px" :rules="questionRules" ref="questionFormRef">
        <el-form-item label="题目内容" prop="content">
          <el-input
              v-model="questionForm.content"
              type="textarea"
              :rows="3"
              placeholder="请输入题目内容"
              maxlength="1000"
              show-word-limit/>
        </el-form-item>
        <el-form-item label="图片">
          <div class="image-upload-container">
            <div class="image-upload-area">
              <el-upload
                  class="question-upload"
                  :auto-upload="false"
                  accept="image/*"
                  :show-file-list="false"
                  :on-change="handleImageChange">
                <template #default>
                  <div class="upload-content">
                    <el-icon class="upload-icon"><Plus /></el-icon>
                    <div class="upload-text">点击或拖拽图片到此处上传</div>
                    <div class="upload-tip">支持 jpg、png 格式，大小不超过 5MB</div>
                  </div>
                </template>
              </el-upload>
            </div>

            <div v-if="previewImage" class="image-preview-area">
              <div class="preview-header">
                <span>图片预览</span>
                <el-button
                    type="danger"
                    size="small"
                    class="delete-btn"
                    @click="clearPreviewImage"
                    :disabled="submitting">
                  <el-icon><Delete /></el-icon>
                  移除图片
                </el-button>
              </div>
              <el-image
                  class="preview-image"
                  :src="previewImage"
                  fit="contain">
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                    <span>图片加载失败</span>
                  </div>
                </template>
              </el-image>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="答案解析" prop="answer">
          <el-input
              v-model="questionForm.answer"
              type="textarea"
              :rows="3"
              placeholder="请输入答案解析"
              maxlength="1000"
              show-word-limit/>
          <div class="form-tip">可以先不填写，之后让AI帮你生成答案</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="questionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleQuestionSubmit" :loading="submitting">
            {{ editingQuestion ? '保存修改' : '添加错题' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </main-layouts>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useMistakenQuestionStore } from '../stores/mistaken_question'
import MainLayouts from "../layouts/MainLayouts.vue";
import { useRouter } from 'vue-router'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { Document } from '@element-plus/icons-vue'

const questionStore = useMistakenQuestionStore()
const router = useRouter()

// 响应式变量
const activeList = ref([])
const listDialogVisible = ref(false)
const questionDialogVisible = ref(false)
const editingList = ref(null)
const editingQuestion = ref(null)
const submitting = ref(false)
const listFormRef = ref(null)
const questionFormRef = ref(null)
const previewImage = ref('')
const showOnlyFavorites = ref(false)

const listForm = ref({ name: '' })
const questionForm = ref({
  content: '',
  image: null,
  is_image: false,
  answer: ''
})

// 表单验证规则
const listRules = {
  name: [
    { required: true, message: '请输入错题集名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const questionRules = {
  content: [
    { required: true, message: '请输入题目内容', trigger: 'blur' },
    { max: 1000, message: '内容不能超过1000个字符', trigger: 'blur' }
  ],
  answer: [
    { max: 1000, message: '答案解析不能超过1000个字符', trigger: 'blur' }
  ]
}

// 在组件挂载时获取错题列表
onMounted(async () => {
  try {
    await questionStore.fetchLists()
  } catch (error) {
    console.error('获取错题列表失败:', error)
    ElMessage.error('获取错题列表失败')
  }
})

// 方法
const showCreateListDialog = () => {
  editingList.value = null
  listForm.value = { name: '' }
  setTimeout(() => {
    listDialogVisible.value = true
    nextTick(() => {
      if (listFormRef.value) {
        listFormRef.value.resetFields()
      }
    })
  }, 0)
}

const handleListSubmit = async () => {
  if (!listFormRef.value) return

  try {
    await listFormRef.value.validate()
    submitting.value = true

    if (!listForm.value.name || listForm.value.name.trim() === '') {
      ElMessage.warning('错题集名称不能为空')
      submitting.value = false
      return
    }

    if (editingList.value) {
      await questionStore.updateList(editingList.value.question_list_id, listForm.value)
      ElMessage.success('错题集已更新')
    } else {
      await questionStore.createList(listForm.value)
      ElMessage.success('错题集已创建')
    }

    // 重置表单和关闭弹窗
    setTimeout(() => {
      listDialogVisible.value = false
      listForm.value = { name: '' }
      editingList.value = null

      // 刷新列表
      questionStore.fetchLists()
    }, 100)
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.msg || (editingList.value ? '更新错题集失败' : '创建错题集失败'))
  } finally {
    submitting.value = false
  }
}

const showCreateQuestionDialog = () => {
  editingQuestion.value = null
  questionForm.value = {
    content: '',
    image: null,
    is_image: false,
    answer: ''
  }
  previewImage.value = ''

  setTimeout(() => {
    questionDialogVisible.value = true
    nextTick(() => {
      if (questionFormRef.value) {
        questionFormRef.value.resetFields()
      }
    })
  }, 0)
}

const handleQuestionSubmit = async () => {
  if (!questionFormRef.value) return

  try {
    await questionFormRef.value.validate()
    submitting.value = true

    const submitData = {
      content: questionForm.value.content || '',
      image: questionForm.value.image || null,
      is_image: questionForm.value.is_image || false
    }

    // 立即关闭弹窗，提升用户体验
    questionDialogVisible.value = false

    // 显示AI正在识别图片的提示
    if (submitData.is_image && submitData.image) {
      ElMessage({
        message: 'AI正在识别图片，请稍候...',
        type: 'info',
        duration: 3000
      })
    }

    if (editingQuestion.value) {
      await questionStore.updateQuestion(editingQuestion.value.question_id, submitData)
      ElMessage.success('错题已更新')
    } else {
      submitData.question_list_id = questionStore.currentList.question_list_id
      await questionStore.createQuestion(submitData)
      ElMessage.success('错题已添加')
    }

    resetForm()
  } catch (error) {
    console.error('操作失败:', error)
    const errorMsg = error.response?.data?.msg || '操作失败'
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  questionForm.value = {
    content: '',
    image: null,
    is_image: false,
    answer: ''
  }
  previewImage.value = ''
  editingQuestion.value = null
}

const handleImageChange = (file) => {
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }

  const isImage = file.raw.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('请上传图片文件!')
    return false
  }

  const reader = new FileReader()
  reader.readAsDataURL(file.raw)
  reader.onload = (e) => {
    const base64Data = e.target.result
    // 更新图片数据和预览
    questionForm.value.image = base64Data.split(',')[1]
    questionForm.value.is_image = true
    previewImage.value = base64Data
    console.log('图片已加载，预览URL已更新', '图片大小:', Math.round(base64Data.length/1024), 'KB')
  }
  reader.onerror = (e) => {
    console.error('图片读取失败', e)
    ElMessage.error('图片读取失败，请重试')
    questionForm.value.image = null
    questionForm.value.is_image = false
    previewImage.value = ''
  }
}

const handleListSelect = async (list) => {
  questionStore.setCurrentList(list)
  if (list.question_list_id) {
    await questionStore.fetchQuestions(list.question_list_id)
  }
}

const editList = (list) => {
  editingList.value = list
  listForm.value = { name: list.name }
  listDialogVisible.value = true
}

const deleteList = async (listId) => {
  try {
    await questionStore.deleteList(listId)
    ElMessage.success('错题集已删除')
  } catch (error) {
    ElMessage.error('删除错题集失败')
  }
}

const editQuestion = (question) => {
  console.log('开始编辑错题:', question.question_id);

  // 设置当前正在编辑的问题
  editingQuestion.value = question;

  // 初始化表单数据
  questionForm.value = {
    content: question.content || '',
    image: null, // 初始不设置图片数据，等待用户上传
    is_image: question.is_image || false,
    answer: question.answer || ''
  };

  // 设置预览图片
  if (question.is_image && question.image_url) {
    console.log('错题含有图片，设置预览图:', question.image_url);
    previewImage.value = question.image_url;
  } else {
    previewImage.value = '';
    console.log('错题没有图片或图片URL为空');

    // 如果问题标记为图片但实际没有URL，强制修正is_image状态
    if (question.is_image && !question.image_url) {
      console.log('警告：问题被标记为图片类型但没有图片URL，已修正is_image状态');
      questionForm.value.is_image = false;
    }
  }

  // 显示编辑对话框
  questionDialogVisible.value = true;

  // 在下一个tick恢复表单验证状态
  nextTick(() => {
    if (questionFormRef.value) {
      questionFormRef.value.clearValidate();
    }
  });
}

const deleteQuestion = async (questionId) => {
  try {
    await questionStore.deleteQuestion(questionId)
    ElMessage.success('错题已删除')
  } catch (error) {
    ElMessage.error('删除错题失败')
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const toggleAnswer = (question) => {
  question.showAnswer = !question.showAnswer
}

const toggleSimilar = (question) => {
  question.showSimilar = !question.showSimilar
}

const toggleSimilarAnswer = (question) => {
  question.showSimilarAnswer = !question.showSimilarAnswer
}

const generateAnswer = async (question) => {
  try {
    await questionStore.generateAnswer(question.question_id)
    question.showAnswer = true
  } catch (error) {
    console.error('生成答案失败:', error)
    ElMessage.error('生成答案失败，请稍后重试')
  }
}

const generateSimilar = async (question) => {
  try {
    await questionStore.generateSimilarQuestion(question.question_id)
    question.showSimilar = true
  } catch (error) {
    console.error('生成相似题目失败:', error)
    ElMessage.error('生成相似题目失败，请稍后重试')
  }
}

const generateSimilarAnswer = async (question) => {
  try {
    if (!question.similar_question) {
      ElMessage.warning('请先生成相似题目')
      return
    }
    await questionStore.generateSimilarAnswer(question.question_id)
    question.showSimilarAnswer = true
  } catch (error) {
    console.error('生成相似题目答案失败:', error)
    ElMessage.error('生成相似题目答案失败，请稍后重试')
  }
}

const clearPreviewImage = () => {
  console.log('清除预览图片')
  previewImage.value = ''
  questionForm.value.image = null
  questionForm.value.is_image = false
}

const toggleFavorite = async (question) => {
  try {
    await questionStore.toggleFavorite(question.question_id)
  } catch (error) {
    ElMessage.error('更新收藏状态失败')
  }
}

// 添加切换只看收藏的方法
const toggleShowOnlyFavorites = () => {
  showOnlyFavorites.value = !showOnlyFavorites.value
}

// 修改显示的问题列表，添加收藏过滤
const filteredQuestions = computed(() => {
  if (!showOnlyFavorites.value) {
    return questionStore.questions
  }
  return questionStore.questions.filter(q => q.is_favorite)
})

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
      throwOnError: false,
      strict: false,
      trust: true,
      macros: {
        "\\RR": "\\mathbb{R}",
        "\\NN": "\\mathbb{N}",
        "\\ZZ": "\\mathbb{Z}",
        "\\CC": "\\mathbb{C}"
      },
      fleqn: false,
      leqno: false,
      output: "html"
    })
  } catch (e) {
    console.error('Math rendering error:', e)
    return text
  }
}

// 添加Markdown渲染函数
const renderMarkdown = (text) => {
  if (!text) return ''

  // 先提取所有数学公式并保存
  const mathExpressions = []
  let mathId = 0

  // 用占位符替换所有数学公式
  text = text.replace(/\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)/g, (match, display, inline) => {
    const formula = display || inline
    const isDisplay = !!display
    const placeholder = `MATH_PLACEHOLDER_${mathId}`
    mathExpressions.push({
      placeholder,
      formula,
      isDisplay
    })
    mathId++
    return placeholder
  })

  // 渲染Markdown
  let html = marked(text)

  // 还原数学公式
  mathExpressions.forEach(({ placeholder, formula, isDisplay }) => {
    const renderedMath = renderMath(formula, isDisplay)
    html = html.replace(placeholder, renderedMath)
  })

  return html
}

// 修改问题卡片中的内容渲染
const renderContent = (content) => {
  return renderMarkdown(content)
}
</script>

<style scoped>
.dashboard-container {
  display: flex;
  gap: 24px;
  padding: 24px;
  height: calc(100vh - 64px);
  background: #f5f7fa;
}

.side-widgets {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-left: 50px;
}

.widget-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.widget-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(108, 93, 211, 0.1);
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stats-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
  position: relative;
  padding-left: 12px;
}

.stats-header h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background: linear-gradient(to bottom, #6c5dd3, #8e6cff);
  border-radius: 2px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  border-radius: 12px;
  background: #ffffff;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.1);
}

.stat-item.total .stat-value {
  color: #6c5dd3;
  font-weight: 600;
}

.stat-item.image .stat-value {
  color: #33d9b2;
  font-weight: 600;
}

.stat-item.text .stat-value {
  color: #ffb142;
  font-weight: 600;
}

.stat-item .stat-label {
  font-size: 13px;
  color: #606266;
  margin-top: 4px;
}

.list-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.widget-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
  position: relative;
  padding-left: 12px;
}

.widget-header h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background: linear-gradient(to bottom, #6c5dd3, #8e6cff);
  border-radius: 2px;
}

.create-list-btn {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  box-shadow: 0 4px 8px rgba(108, 93, 211, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.create-list-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(108, 93, 211, 0.3);
}


.list-container {
  flex: 1;
  overflow: hidden;
}

.list-title {
  width: 100%;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0;
  background: transparent;
  border: none;
  position: relative;
  z-index: 1;
}

.list-title-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.list-name {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.question-count {
  font-size: 13px;
  padding: 2px 12px;
  background: #f5f7fa;
  color: #606266;
  border: none;
  box-shadow: none;
}

.view-btn {
  color: #fff;
  background: #6c5dd3;
  border: none;
  padding: 4px 12px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 4px;
}

.view-btn:hover {
  opacity: 0.9;
  background: #5c4db3;
}

.view-btn .el-icon {
  font-size: 14px;
  color: #fff;
}

.list-content {
  padding: 0 20px 16px;
}

.list-actions {
  display: flex;
  justify-content: flex-start;
  gap: 24px;
  padding: 0;
  margin-top: 8px;
}

.action-left, .action-right {
  flex: none;
}

.list-actions button {
  color: #6c5dd3;
  background: none;
  border: none;
  padding: 0;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.list-actions button:hover {
  opacity: 0.8;
}

:deep(.el-collapse-item__content) {
  padding: 0;
  background: transparent;
}

.questions-content {
  flex: 1;
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.questions-content:hover {
  box-shadow: 0 8px 30px rgba(108, 93, 211, 0.1);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.content-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
  position: relative;
  padding-left: 16px;
}

.content-header h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 24px;
  background: linear-gradient(to bottom, #6c5dd3, #8e6cff);
  border-radius: 3px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.questions-scrollbar {
  flex: 1;
  overflow: hidden;
}

.questions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  padding: 20px;
}

.question-card {
  border-radius: 16px;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  position: relative;
  animation: cardFadeIn 0.5s ease-out;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.question-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 28px rgba(108, 93, 211, 0.15);
}

.question-card:after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #6c5dd3, #8674ff);
  transform: scaleX(0);
  transform-origin: 0 50%;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.question-card:hover:after {
  transform: scaleX(1);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-date {
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 6px;
}

.question-date:before {
  content: '\f073';
  font-family: 'Element Icons';
  font-size: 14px;
  color: #6c5dd3;
}

.question-content {
  margin: 16px 0;
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  background: #f9fafc;
  padding: 18px;
  border-radius: 10px;
  border-left: 3px solid #6c5dd3;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.text-section {
  padding: 16px;
  line-height: 1.8;
  background: #f9fafc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  position: relative;
}

.section-label {
  position: absolute;
  top: -10px;
  left: 12px;
  background: transparent;
  color: #909399;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.5px;
  box-shadow: none;
}

.image-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
}

.question-image {
  max-height: 220px;
  width: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: zoom-in;
  will-change: transform;
  backface-visibility: hidden;
  transform: translateZ(0);
  display: block;
}

.question-image:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 20px rgba(108, 93, 211, 0.2);
}

:deep(.el-image-viewer__wrapper) {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  z-index: 2000;
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

:deep(.el-image-viewer__wrapper.is-active) {
  opacity: 1;
}

:deep(.el-image-viewer__img) {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
  transform: scale(0.95);
  transition: transform 0.3s ease;
  will-change: transform;
  backface-visibility: hidden;
}

:deep(.el-image-viewer__img.is-active) {
  transform: scale(1);
}

:deep(.el-image-viewer__canvas) {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  transform: translateZ(0);
  will-change: transform;
}

:deep(.el-image-viewer__actions) {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 20px;
  padding: 8px 16px;
  display: flex;
  gap: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

:deep(.el-image-viewer__wrapper.is-active .el-image-viewer__actions) {
  opacity: 1;
}

:deep(.el-image-viewer__actions__inner) {
  display: flex;
  gap: 16px;
}

:deep(.el-image-viewer__actions__inner i) {
  color: white;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  transform: translateZ(0);
}

:deep(.el-image-viewer__actions__inner i:hover) {
  transform: scale(1.1);
  color: #6c5dd3;
}

.section {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  margin-top: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.section:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: linear-gradient(to right, #f9fafc, #f5f7ff);
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.section-header:hover {
  background: linear-gradient(to right, #f5f7ff, #eff1ff);
}

.section-title {
  font-weight: 500;
  color: #303133;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title i {
  color: #6c5dd3;
  font-size: 16px;
}

.section-content {
  padding: 16px;
  background-color: #fff;
  max-height: 300px;
  overflow-y: auto;
  position: relative;
}

.section-content::-webkit-scrollbar {
  width: 6px;
}

.section-content::-webkit-scrollbar-thumb {
  background-color: rgba(108, 93, 211, 0.3);
  border-radius: 3px;
}

.section-content::-webkit-scrollbar-track {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.empty-text {
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 20px;
  background: #f9fafc;
  border-radius: 8px;
  border: 1px dashed #d8e0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-text:before {
  content: '';
  display: block;
  width: 40px;
  height: 40px;
  background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOTA5Mzk5IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgY2xhc3M9ImZlYXRoZXIgZmVhdGhlci1pbmZvIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCI+PC9jaXJjbGU+PHBhdGggZD0iTTEyIDhWMTIiPjwvcGF0aD48cGF0aCBkPSJNMTIgMTZoLjAxIj48L3BhdGg+PC9zdmc+') no-repeat center center;
  opacity: 0.5;
}

.answer-text,
.similar-text,
.similar-answer-text {
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: #303133;
  padding: 16px;
  background: #f9fafc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  position: relative;
}

.answer-text {
  border-left: 3px solid #67c23a;
}

.similar-text {
  border-left: 3px solid #e6a23c;
}

.similar-answer-text {
  border-left: 3px solid #409eff;
}

.answer-text:before,
.similar-text:before,
.similar-answer-text:before {
  content: '';
  display: none;
}

/* 对话框样式优化 */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(108, 93, 211, 0.15);
  margin-top: 6vh;
  transform: translateY(0);
  opacity: 1;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 90%;
}

@media screen and (max-width: 768px) {
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto !important;
  }
}

:deep(.el-dialog.dialog-fade-enter-from) {
  transform: translateY(-16px);
  opacity: 0;
}

:deep(.el-dialog.dialog-fade-leave-to) {
  transform: translateY(16px);
  opacity: 0;
}

:deep(.el-dialog__header) {
  margin: 0;
  padding: 16px 20px;
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  position: relative;
}

:deep(.el-dialog__title) {
  color: white;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

:deep(.el-dialog__headerbtn) {
  top: 16px;
  right: 16px;
  z-index: 10;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}

:deep(.el-dialog__footer) {
  padding: 12px 24px 16px;
  border-top: 1px solid #ebeef5;
  background: #f9fafc;
}

/* 表单样式优化 */
:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
  padding-bottom: 6px;
  font-size: 14px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
  transition: all 0.3s ease;
  padding: 0 12px;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.1) !important;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6c5dd3, 0 4px 12px rgba(108, 93, 211, 0.1) !important;
}

:deep(.el-input__inner) {
  height: 36px;
  font-size: 14px;
  color: #303133;
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 10px 12px;
  min-height: 100px !important;
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s ease;
  resize: vertical;
}

:deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px #6c5dd3, 0 4px 12px rgba(108, 93, 211, 0.1) !important;
}

/* 表单项间距 */
:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

/* 表单提示信息 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  padding-left: 2px;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-tip:before {
  content: '';
  display: inline-block;
  width: 14px;
  height: 14px;
  background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjOTA5Mzk5IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgY2xhc3M9ImZlYXRoZXIgZmVhdGhlci1pbmZvIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCI+PC9jaXJjbGU+PHBhdGggZD0iTTEyIDhWMTIiPjwvcGF0aD48cGF0aCBkPSJNMTIgMTZoLjAxIj48L3BhdGg+PC9zdmc+') no-repeat center center;
  background-size: contain;
  opacity: 0.6;
}

/* 对话框按钮样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 0;
}

:deep(.dialog-footer .el-button) {
  min-width: 80px;
  height: 36px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px dashed #d8e0f0;
}

.preview-header span {
  font-weight: 500;
  color: #303133;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.preview-header span:before {
  content: '';
  display: inline-block;
  width: 16px;
  height: 16px;
  background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNmM1ZGQzIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMiIgcnk9IjIiPjwvcmVjdD48Y2lyY2xlIGN4PSI4LjUiIGN5PSI4LjUiIHI9IjEuNSI+PC9jaXJjbGU+PHBvbHlsaW5lIHBvaW50cz0iMjEgMTUgMTYgMTAgNSAyMSI+PC9wb2x5bGluZT48L3N2Zz4=') no-repeat center center;
  background-size: contain;
}

.preview-image {
  max-width: 100%;
  max-height: 220px;
  object-fit: contain;
  border-radius: 10px;
  margin-top: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.preview-image:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(108, 93, 211, 0.15);
}

/* 图片错误状态 */
.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  background: #fff5f5;
  border-radius: 10px;
  border: 1px dashed #ffa39e;
}

.image-error .el-icon {
  font-size: 40px;
  color: #ff4d4f;
}

.image-error span {
  font-size: 15px;
  color: #ff4d4f;
  font-weight: 500;
}

/* 删除按钮样式 */
.preview-header .delete-btn {
  padding: 6px 12px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4d4f, #ff7875);
  border: none;
  color: white;
  font-size: 13px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.preview-header .delete-btn:hover {
  background: linear-gradient(135deg, #ff7875, #ff9c9c);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.2);
}

.preview-header .delete-btn .el-icon {
  font-size: 14px;
}

.preview-header .delete-btn.is-disabled {
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  color: rgba(0, 0, 0, 0.25);
  cursor: not-allowed;
  box-shadow: none;
}

/* 动画效果 */
.el-dialog-fade-enter-active {
  animation: dialog-fade-in 0.3s;
}

.el-dialog-fade-leave-active {
  animation: dialog-fade-out 0.3s;
}

@keyframes dialog-fade-in {
  0% {
    transform: translate3d(0, -16px, 0);
    opacity: 0;
  }
  100% {
    transform: translate3d(0, 0, 0);
    opacity: 1;
  }
}

@keyframes dialog-fade-out {
  0% {
    transform: translate3d(0, 0, 0);
    opacity: 1;
  }
  100% {
    transform: translate3d(0, 16px, 0);
    opacity: 0;
  }
}

/* 图片上传和预览区域 */
.image-upload-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 8px;
}

.image-upload-area {
  width: 100%;
}

.image-preview-area {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f9fafc;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #e8f0fe;
  animation: fadeIn 0.3s ease;
}

:deep(.dialog-footer .el-button--default) {
  border-color: #dcdfe6;
  color: #606266;
  background-color: #f9fafc;
}

:deep(.dialog-footer .el-button--default:hover) {
  border-color: #c0c4cc;
  color: #303133;
  background-color: #f5f7fa;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

:deep(.dialog-footer .el-button--primary) {
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  border: none;
  color: white;
  box-shadow: 0 4px 10px rgba(108, 93, 211, 0.2);
}

:deep(.dialog-footer .el-button--primary:hover) {
  background: linear-gradient(135deg, #5c4db3, #7964e0);
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(108, 93, 211, 0.3);
}

:deep(.dialog-footer .el-button--primary.is-loading) {
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  opacity: 0.8;
  pointer-events: none;
}

/* 上传区域样式优化 */
.question-upload {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: #f9fafc;
  border: 2px dashed #d8e0f0;
  border-radius: 14px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.question-upload:hover {
  border-color: #6c5dd3;
  background: #f5f7ff;
  transform: translateY(-2px);
}

.question-upload:active {
  transform: translateY(0);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 28px;
  color: #6c5dd3;
  opacity: 0.7;
  transition: all 0.3s ease;
}

.question-upload:hover .upload-icon {
  transform: scale(1.1);
  opacity: 1;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.header-actions .el-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  box-shadow: 0 4px 8px rgba(108, 93, 211, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(108, 93, 211, 0.3);
}

.section-header .el-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  box-shadow: 0 4px 8px rgba(108, 93, 211, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
}

.section-header .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(108, 93, 211, 0.3);
}

.section-header .el-button.is-loading {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  opacity: 0.8;
}

.section-header .el-button .el-icon {
  font-size: 14px;
  margin-right: 4px;
}

.empty-description {
  color: #606266;
  font-size: 14px;
  margin: 0;
  text-align: center;
  line-height: 1.5;
}

.add-question-btn {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  box-shadow: 0 4px 8px rgba(108, 93, 211, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
}

.add-question-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(108, 93, 211, 0.3);
}

.add-question-btn .el-icon {
  font-size: 14px;
}

.view-btn {
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  border: none;
  box-shadow: 0 4px 10px rgba(108, 93, 211, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  height: 28px;
  font-size: 13px;
}

.view-btn:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, #5c4db3, #7964e0);
  box-shadow: 0 6px 12px rgba(108, 93, 211, 0.3);
}

.view-btn .el-icon {
  font-size: 14px;
}

.favorite-btn {
  padding: 8px;
  border: none;
  background: transparent;
}

.favorite-btn:hover {
  background: rgba(108, 93, 211, 0.1);
}

.favorite-btn .el-icon {
  font-size: 16px;
  transition: all 0.3s ease;
}

/* 未收藏状态 */
.favorite-btn:not(.is-favorite) .el-icon {
  color: #909399;
}

/* 已收藏状态 */
.favorite-btn.is-favorite .el-icon {
  color: #f7ba2a;
}

/* 悬停效果 */
.favorite-btn:not(.is-favorite):hover .el-icon {
  color: #f7ba2a;
  opacity: 0.7;
}

/* 点击动画 */
.favorite-btn.is-favorite .el-icon {
  animation: favorite-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes favorite-pop {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.header-actions .el-button.is-active {
  background: linear-gradient(to right, #f7ba2a, #ffd700);
  color: white;
  border: none;
}

.header-actions .el-button.is-active:hover {
  background: linear-gradient(to right, #e6a817, #ffd700);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(247, 186, 42, 0.3);
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

/* 修改文本内容样式 */
.text-section {
  padding: 16px;
  line-height: 1.8;
  background: #f9fafc;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  position: relative;
}

.content-text {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  word-break: break-word;
}

:deep(.content-text p) {
  margin: 0.5em 0;
}

:deep(.content-text code) {
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

:deep(.content-text pre) {
  background-color: #f5f5f5;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

:deep(.content-text blockquote) {
  border-left: 4px solid #6c5dd3;
  margin: 0;
  padding-left: 1em;
  color: #666;
}

:deep(.content-text ul),
:deep(.content-text ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

:deep(.content-text h1),
:deep(.content-text h2),
:deep(.content-text h3),
:deep(.content-text h4),
:deep(.content-text h5),
:deep(.content-text h6) {
  margin: 1em 0 0.5em;
  font-weight: 600;
  line-height: 1.4;
}

:deep(.content-text h1) { font-size: 1.5em; }
:deep(.content-text h2) { font-size: 1.3em; }
:deep(.content-text h3) { font-size: 1.2em; }
:deep(.content-text h4) { font-size: 1.1em; }
:deep(.content-text h5) { font-size: 1em; }
:deep(.content-text h6) { font-size: 0.9em; }

:deep(.content-text table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

:deep(.content-text th),
:deep(.content-text td) {
  border: 1px solid #e4e7ed;
  padding: 8px;
  text-align: left;
}

:deep(.content-text th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.content-text img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

:deep(.content-text a) {
  color: #6c5dd3;
  text-decoration: none;
  border-bottom: 1px solid #6c5dd3;
  transition: all 0.3s ease;
}

:deep(.content-text a:hover) {
  color: #8674ff;
  border-bottom-color: #8674ff;
}

:deep(.content-text hr) {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 1.5em 0;
}

:deep(.content-text .task-list-item) {
  list-style-type: none;
  margin-left: -1.5em;
}

:deep(.content-text .task-list-item-checkbox) {
  margin-right: 0.5em;
}

.custom-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 0;
}

.empty-image-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 24px;
  width: 100%;
}

.empty-icon {
  font-size: 80px;
  color: #909399;
  opacity: 0.5;
}
</style>
