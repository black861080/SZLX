<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search as SearchIcon } from '@element-plus/icons-vue'
import MainLayouts from "../layouts/MainLayouts.vue"
import axios from '../utils/axios'
import { useUserStore } from '../stores/user'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { marked } from 'marked'

const userStore = useUserStore()
const keyword = ref('')
const searchKeyword = ref('')
const searchResults = ref([])
const isLoading = ref(false)
const noResults = ref(false)
const hasSearched = ref(false)
const searchHistory = ref([])
const searchType = ref('notes')

// 添加marked配置
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

// 执行搜索
const performSearch = async () => {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  isLoading.value = true
  hasSearched.value = true
  noResults.value = false
  searchResults.value = []
  searchKeyword.value = keyword.value.trim()

  try {
    const endpoint = searchType.value === 'notes'
      ? '/notes_service/note/search'
      : '/mistaken_question_service/question/search'

    const response = await axios.get(endpoint, {
      params: { keyword: searchKeyword.value }
    })

    searchResults.value = response.data.data
    noResults.value = searchResults.value.length === 0
    await getSearchHistory()
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败，请稍后重试')
    noResults.value = true
  } finally {
    isLoading.value = false
  }
}

// 处理回车键搜索
const handleKeyDown = (event) => {
  if (event.key === 'Enter') {
    performSearch()
  }
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取匹配类型的文本描述
const getMatchTypeText = (item) => {
  const matchTypes = []

  if (searchType.value === 'notes') {
    if (item.match_type.includes('image')) {
      matchTypes.push(`图片中包含"${searchKeyword.value}"`)
    }
    if (item.match_type.includes('audio')) {
      matchTypes.push(`录音中包含"${searchKeyword.value}"`)
    }
  } else {
    if (item.match_type.includes('content')) {
      matchTypes.push(`题目中包含"${searchKeyword.value}"`)
    }
    if (item.match_type.includes('answer')) {
      matchTypes.push(`答案中包含"${searchKeyword.value}"`)
    }
    if (item.match_type.includes('image')) {
      matchTypes.push(`图片中包含"${searchKeyword.value}"`)
    }
    if (item.match_type.includes('similar_question')) {
      matchTypes.push(`相似题目中包含"${searchKeyword.value}"`)
    }
    if (item.match_type.includes('similar_answer')) {
      matchTypes.push(`相似答案中包含"${searchKeyword.value}"`)
    }
  }

  return matchTypes.join('，')
}

// 修改数学公式渲染函数
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

// 修改渲染内容函数
const renderContent = (text) => {
  return renderMarkdown(text)
}

// 修改高亮显示关键词函数
const highlightKeyword = (text) => {
  if (!text) return ''
  // 先渲染内容
  const rendered = renderContent(text)
  
  // 创建一个临时的DOM元素来解析HTML
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = rendered
  
  // 获取所有文本节点并高亮关键词，但避开数学公式
  const highlightTextNodes = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      // 仅处理文本节点
      if (node.textContent.includes(searchKeyword.value)) {
        const span = document.createElement('span')
        span.innerHTML = node.textContent.replace(
          new RegExp(searchKeyword.value, 'gi'), 
          match => `<span class="highlight">${match}</span>`
        )
        node.parentNode.replaceChild(span, node)
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      // 跳过所有katex相关元素
      if (node.classList && (
          node.classList.contains('katex') || 
          node.classList.contains('katex-html') || 
          node.classList.contains('katex-mathml')
        )) {
        return
      }
      
      // 递归处理子节点
      Array.from(node.childNodes).forEach(child => {
        highlightTextNodes(child)
      })
    }
  }
  
  // 处理所有节点
  highlightTextNodes(tempDiv)
  
  return tempDiv.innerHTML
}

// 获取搜索历史记录
const getSearchHistory = async () => {
  try {
    const response = await axios.get('/search_history_service/recent')
    searchHistory.value = response.data.data
  } catch (error) {
    console.error('获取搜索历史失败:', error)
  }
}

// 删除搜索历史记录
const deleteSearchHistory = async (historyId) => {
  try {
    await axios.delete(`/search_history_service/delete/${historyId}`)
    ElMessage.success('删除成功')
    await getSearchHistory()
  } catch (error) {
    console.error('删除搜索历史失败:', error)
    ElMessage.error('删除失败')
  }
}

// 点击历史记录进行搜索
const searchFromHistory = (historyKeyword) => {
  keyword.value = historyKeyword
  performSearch()
}

// 在组件挂载时获取搜索历史
onMounted(() => {
  getSearchHistory()
})
</script>

<template>
  <main-layouts>
    <div class="search-container">
      <div class="search-header">
        <h2>搜索</h2>
        <div class="search-controls">
          <div class="custom-button-group">
            <button
              class="custom-button"
              :class="{ active: searchType === 'notes' }"
              @click="searchType = 'notes'"
            >
              笔记
            </button>
            <button
              class="custom-button"
              :class="{ active: searchType === 'questions' }"
              @click="searchType = 'questions'"
            >
              错题
            </button>
          </div>
          <div class="search-box">
            <el-input
              v-model="keyword"
              :placeholder="searchType === 'notes' ? '请输入搜索关键词' : '请输入错题搜索关键词'"
              class="search-input"
              @keydown="handleKeyDown"
              clearable>
              <template #suffix>
                <el-button
                  :icon="SearchIcon"
                  circle
                  @click="performSearch"
                  :loading="isLoading"
                  class="search-button" />
              </template>
            </el-input>
          </div>
        </div>
      </div>

      <!-- 添加搜索历史区域 -->
      <div class="search-history" v-if="!hasSearched && searchHistory.length > 0">
        <h3>最近搜索</h3>
        <div class="history-tags">
          <el-tag
            v-for="history in searchHistory"
            :key="history.history_id"
            class="history-tag"
            closable
            @click="searchFromHistory(history.keyword)"
            @close.stop="deleteSearchHistory(history.history_id)"
          >
            {{ history.keyword }}
          </el-tag>
        </div>
      </div>

      <div class="search-results" v-if="hasSearched">
        <div class="results-header" v-if="!isLoading">
          <span v-if="searchResults.length > 0">
            找到 {{ searchResults.length }} 条相关{{ searchType === 'notes' ? '笔记' : '错题' }}
          </span>
        </div>

        <div class="loading-container" v-if="isLoading">
          <el-loading-icon />
          <p>正在搜索中...</p>
        </div>

        <el-empty v-else-if="noResults" :description="`未找到相关${searchType === 'notes' ? '笔记' : '错题'}`" />

        <div class="results-list" v-else>
          <!-- 笔记搜索结果 -->
          <template v-if="searchType === 'notes'">
            <div v-for="note in searchResults" :key="note.note_id" class="result-card">
              <div class="result-header">
                <div class="chapter-info">
                  <span class="chapter-name">{{ note.chapter_name }}</span>
                  <span class="result-date">{{ formatDate(note.created_at) }}</span>
                </div>
                <div class="match-type" v-if="getMatchTypeText(note)">
                  {{ getMatchTypeText(note) }}
                </div>
              </div>

              <div class="result-content">
                <div v-if="note.is_image" class="image-content">
                  <img :src="note.image_url" alt="笔记图片" class="note-image" />
                </div>

                <div v-if="note.is_audio" class="audio-content">
                  <audio controls :src="note.audio_url" class="note-audio"></audio>
                </div>

                <div v-if="note.words" class="text-content" v-html="highlightKeyword(note.words)"></div>
              </div>
            </div>
          </template>

          <!-- 错题搜索结果 -->
          <template v-else>
            <div v-for="question in searchResults" :key="question.question_id" class="result-card">
              <div class="result-header">
                <div class="chapter-info">
                  <span class="chapter-name">{{ question.question_list_name }}</span>
                  <span class="result-date">{{ formatDate(question.created_at) }}</span>
                </div>
                <div class="match-type" v-if="getMatchTypeText(question)">
                  {{ getMatchTypeText(question) }}
                </div>
              </div>

              <div class="result-content">
                <div v-if="question.is_image" class="image-content">
                  <img :src="question.image_url" alt="错题图片" class="note-image" />
                </div>

                <div class="text-content">
                  <div class="question-content" v-if="question.content">
                    <strong>题目：</strong>
                    <div class="content-wrapper" v-html="highlightKeyword(question.content)"></div>
                  </div>
                  <div class="answer-content" v-if="question.answer">
                    <strong>答案解析：</strong>
                    <div class="content-wrapper" v-html="highlightKeyword(question.answer)"></div>
                  </div>
                  <div class="similar-content" v-if="question.similar_question">
                    <strong>相似题目：</strong>
                    <div class="content-wrapper" v-html="highlightKeyword(question.similar_question)"></div>
                  </div>
                  <div class="similar-answer-content" v-if="question.similar_answer">
                    <strong>相似题目答案：</strong>
                    <div class="content-wrapper" v-html="highlightKeyword(question.similar_answer)"></div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="search-placeholder" v-else>
        <div class="placeholder-content">
          <el-icon :size="64" class="placeholder-icon"><SearchIcon /></el-icon>
          <p>输入关键词搜索您的{{ searchType === 'notes' ? '笔记' : '错题' }}</p>
        </div>
      </div>
    </div>
  </main-layouts>
</template>

<style scoped>
.search-container {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-header {
  margin-bottom: 32px;
}

.search-header h2 {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
}

.search-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.custom-button-group {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.custom-button {
  padding: 8px 20px;
  border: 1px solid #e0e0ff;
  border-radius: 8px;
  background: #f0f0ff;
  color: #6c5dd3;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  outline: none;
}

.custom-button:hover {
  background: #e0e0ff;
  border-color: #6c5dd3;
}

.custom-button.active {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border-color: transparent;
  color: #fff;
}

.custom-button.active:hover {
  background: linear-gradient(to right, #8e6cff, #6c5dd3);
  opacity: 0.9;
}

.search-box {
  max-width: 600px;
}

.search-input {
  width: 100%;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6;
  padding: 8px 16px;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #6c5dd3;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #6c5dd3 !important;
}

.search-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  color: white;
}

.search-button:hover {
  opacity: 0.9;
}

.search-results {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 24px;
  min-height: 400px;
}

.results-header {
  margin-bottom: 24px;
  color: #606266;
  font-size: 14px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 16px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  background: #f8f9fe;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-name {
  font-weight: 600;
  color: #303133;
}

.result-date {
  color: #909399;
  font-size: 12px;
}

.match-type {
  color: #6c5dd3;
  font-size: 12px;
  background: #f0f0ff;
  padding: 4px 8px;
  border-radius: 4px;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.image-content, .audio-content, .text-content {
  margin-top: 8px;
}

.note-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.note-audio {
  width: 100%;
  margin-bottom: 8px;
}

/* 优化数学公式相关样式 */
:deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 1em 0;
  margin: 0.5em 0;
  text-align: center;
}

:deep(.katex) {
  font-size: 1.1em;
  line-height: 1.2;
  white-space: normal;
  text-indent: 0;
}

:deep(.katex-html) {
  white-space: normal;
  text-align: left;
}

/* 添加浮动元素清除样式 */
:deep(.katex-display::after) {
  content: "";
  display: table;
  clear: both;
}

/* 确保数学公式容器有足够的空间 */
:deep(.katex-display > .katex) {
  display: inline-block;
  white-space: nowrap;
  max-width: 100%;
  text-align: initial;
}

/* 解决长公式溢出问题 */
:deep(.katex-display > .katex > .katex-html) {
  display: block;
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  text-align: center;
  width: 100%;
}

/* 针对搜索结果中数学公式的特殊处理 */
.content-wrapper :deep(.katex-display) {
  margin: 1em 0;
}

.content-wrapper :deep(.katex) {
  font-size: 1.05em;
}

/* 修复表格内数学公式显示 */
:deep(table .katex) {
  font-size: 1em;
}

/* 修改文本内容样式 */
.text-content {
  color: #303133;
  line-height: 1.6;
  padding: 12px;
  border-radius: 8px;
  background-color: #f9f9fd;
  margin-top: 12px;
}

.question-content,
.answer-content,
.similar-content,
.similar-answer-content {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e0e0ff;
}

.question-content:last-child,
.answer-content:last-child,
.similar-content:last-child,
.similar-answer-content:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.question-content strong,
.answer-content strong,
.similar-content strong,
.similar-answer-content strong {
  color: #6c5dd3;
  margin-right: 8px;
  display: inline-block;
  vertical-align: top;
  background: #f0f0ff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
}

.content-wrapper {
  display: inline-block;
  vertical-align: top;
  max-width: 100%;
  overflow-x: auto;
  padding: 8px 12px;
  margin-top: 8px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(108, 93, 211, 0.05);
}

:deep(.text-content p) {
  margin: 0.5em 0;
}

:deep(.text-content code) {
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

:deep(.text-content pre) {
  background-color: #f5f5f5;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

:deep(.text-content blockquote) {
  border-left: 4px solid #6c5dd3;
  margin: 0;
  padding-left: 1em;
  color: #666;
}

:deep(.text-content ul),
:deep(.text-content ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

:deep(.text-content h1),
:deep(.text-content h2),
:deep(.text-content h3),
:deep(.text-content h4),
:deep(.text-content h5),
:deep(.text-content h6) {
  margin: 1em 0 0.5em;
  font-weight: 600;
  line-height: 1.4;
}

:deep(.text-content h1) { font-size: 1.5em; }
:deep(.text-content h2) { font-size: 1.3em; }
:deep(.text-content h3) { font-size: 1.2em; }
:deep(.text-content h4) { font-size: 1.1em; }
:deep(.text-content h5) { font-size: 1em; }
:deep(.text-content h6) { font-size: 0.9em; }

:deep(.text-content table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

:deep(.text-content th),
:deep(.text-content td) {
  border: 1px solid #e4e7ed;
  padding: 8px;
  text-align: left;
}

:deep(.text-content th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.text-content img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

:deep(.text-content a) {
  color: #6c5dd3;
  text-decoration: none;
  border-bottom: 1px solid #6c5dd3;
  transition: all 0.3s ease;
}

:deep(.text-content a:hover) {
  color: #8674ff;
  border-bottom-color: #8674ff;
}

:deep(.text-content hr) {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 1.5em 0;
}

:deep(.text-content .task-list-item) {
  list-style-type: none;
  margin-left: -1.5em;
}

:deep(.text-content .task-list-item-checkbox) {
  margin-right: 0.5em;
}

.search-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #909399;
}

.placeholder-icon {
  color: #dcdfe6;
}

.search-history {
  margin: 24px 0;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.search-history h3 {
  color: #303133;
  font-size: 16px;
  margin-bottom: 16px;
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.history-tag {
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f0f0ff;
  border-color: #e0e0ff;
  color: #6c5dd3;
}

.history-tag:hover {
  background: #e0e0ff;
  transform: translateY(-2px);
}

:deep(.el-tag .el-tag__close) {
  color: #6c5dd3;
}

:deep(.el-tag .el-tag__close:hover) {
  background-color: #6c5dd3;
  color: #fff;
}

:deep(.highlight) {
  background-color: #ffeaa7;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: bold;
}
</style>
