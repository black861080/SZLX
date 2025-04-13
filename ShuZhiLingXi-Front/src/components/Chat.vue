<template>
  <MainLayouts>
    <!-- 新增弹窗 -->
    <div v-if="showNewChatDialog" class="dialog-mask" @click.self="showNewChatDialog = false">
      <div class="new-chat-dialog">
        <h3>新建对话</h3>
        <input
            v-model="newChatName"
            placeholder="请输入对话名称"
            class="name-input"
            @keyup.enter="confirmNewChat"
        >
        <button class="confirm-btn" @click="confirmNewChat">确认创建</button>
      </div>
    </div>

    <!-- 添加编辑弹窗 -->
    <div v-if="showEditDialog" class="dialog-mask" @click.self="showEditDialog = false">
      <div class="edit-dialog">
        <div class="edit-dialog-header">
          <h3>编辑消息</h3>
          <button class="close-btn" @click="showEditDialog = false">
            <Icon icon="material-symbols:close" />
          </button>
        </div>
        <div class="edit-dialog-body">
          <textarea
              v-model="editingText"
              placeholder="请输入新的消息内容"
              class="edit-textarea"
              @keydown.ctrl.enter="saveEdit"
          ></textarea>
          <div class="textarea-footer">
            <span class="hint">提示：Ctrl + Enter 快捷提交</span>
            <span class="word-count">{{ editingText.length }} 字</span>
          </div>
        </div>
        <div class="edit-dialog-footer">
          <button class="cancel-btn" @click="showEditDialog = false">
            <Icon icon="material-symbols:close" class="btn-icon" />
            取消
          </button>
          <button class="confirm-btn" @click="saveEdit">
            <Icon icon="material-symbols:check" class="btn-icon" />
            确认
          </button>
        </div>
      </div>
    </div>

    <div class="chat-container">
      <!-- 左侧历史对话列表 -->
      <div class="history-sidebar">
        <div class="history-header">
          <h2>历史对话</h2>
          <button class="new-chat-btn" @click="openNewChatDialog">
            <Icon icon="material-symbols:add" />
            新建对话
          </button>
        </div>

        <div class="history-list">
          <div
              v-for="chat in chatLists"
              :key="chat.chat_history_list_id"
              class="history-item"
              :class="{ active: currentChatId === chat.chat_history_list_id }"
              @click="selectChat(chat.chat_history_list_id)"
          >
            <Icon icon="material-symbols:chat" class="chat-icon" />
            <div class="chat-info">
              <span class="chat-name">{{ chat.name }}</span>
              <span class="chat-time">{{ formatDate(chat.created_at) }}</span>
            </div>
            <button class="delete-btn" @click.stop="deleteChat(chat.chat_history_list_id)">
              <Icon icon="material-symbols:delete" />
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="chat-main">
        <!-- 聊天记录显示区域 -->
        <div class="chat-messages" ref="messageContainer">
          <div
              v-for="message in chatDetails"
              :key="message.chat_history_detail_id"
              :class="['message', message.role === 'system' ? 'message-ai' : 'message-user']"
          >
            <transition name="fade">
              <div v-if="!deletedMessages.includes(message.chat_history_detail_id)" class="message-wrapper">
                <div class="message-content">
                  <div v-if="message.is_image" class="image-container">
                    <img :src="message.image_url" alt="上传的图片" />
                    <p class="image-description">{{ message.image_describe }}</p>
                  </div>
                  <!-- 用户消息 -->
                  <div v-if="message.role === 'user'" class="user-message">
                    <div class="message-text" v-if="editingMessageId !== message.chat_history_detail_id">
                      {{ message.words }}
                    </div>
                    <input
                        v-else
                        v-model="editingText"
                        @blur="saveEdit(message)"
                        @keyup.enter="saveEdit(message)"
                        class="edit-input"
                        ref="editInput"
                    />
                  </div>
                  <!-- AI消息 -->
                  <div v-else class="ai-message">
                    <div class="message-text" v-html="renderMarkdown(message.words)"></div>
                  </div>
                </div>
                <!-- 操作按钮 -->
                <div class="message-actions">
                  <button class="action-btn" @click="copyMessage(message.words)" title="复制">
                    <Icon icon="material-symbols:content-copy" />
                  </button>
                  <template v-if="message.role === 'user'">
                    <button class="action-btn" @click="startEdit(message)" title="编辑">
                      <Icon icon="material-symbols:edit" />
                    </button>
                    <button class="action-btn delete-action" @click="deleteMessage(message.chat_history_detail_id)" title="删除">
                      <Icon icon="material-symbols:delete" />
                    </button>
                  </template>
                  <template v-if="message.role === 'system'">
                    <button class="action-btn delete-action" @click="deleteMessage(message.chat_history_detail_id)" title="删除">
                      <Icon icon="material-symbols:delete" />
                    </button>
                  </template>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <div class="new-chat-shortcut-wrapper">
            <button class="new-chat-shortcut" @click="openNewChatDialog">
              <Icon icon="material-symbols:refresh" class="btn-icon" />
              开启新对话
            </button>
          </div>
          <div class="input-container">
            <textarea
                v-model="userInput"
                placeholder="请输入您的问题..."
                @keyup.enter.exact="sendMessage"
            ></textarea>
            <div class="input-actions">
              <button
                class="math-enhance-btn"
                :class="{ active: isMathEnhanced }"
                @click="isMathEnhanced = !isMathEnhanced"
                title="数学增强模式"
              >
                <Icon icon="material-symbols:calculate" />
              </button>
              <label class="upload-btn">
                <Icon icon="material-symbols:image" />
                <input
                    type="file"
                    accept="image/*"
                    @change="handleImageUpload"
                    style="display: none"
                >
              </label>
              <button class="send-btn" @click="sendMessage">
                <Icon icon="material-symbols:send" />
              </button>
            </div>
          </div>
          <div v-if="selectedImage" class="image-preview">
            <img :src="selectedImage" alt="预览图片" />
            <button class="remove-image" @click="removeImage">
              <Icon icon="material-symbols:close" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </MainLayouts>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { Icon } from '@iconify/vue'
import axios from '../utils/axios'
import MainLayouts from "../layouts/MainLayouts.vue"
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const chatStore = useChatStore()
const currentChatId = ref(null)
const userInput = ref('')
const selectedImage = ref(null)
const messageContainer = ref(null)
const isMathEnhanced = ref(false)

// 新增响应式变量
const showNewChatDialog = ref(false)
const newChatName = ref('')

// 添加新的响应式变量
const editingMessageId = ref(null)
const editingText = ref('')
const editInput = ref(null)

// 添加已删除消息的记录
const deletedMessages = ref([])

// 添加编辑弹窗
const showEditDialog = ref(false)
const editingMessage = ref(null)

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
    console.error('Math rendering error:', e)
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

  // 渲染Markdown
  return marked(text)
}

// 打开新建对话弹窗
const openNewChatDialog = () => {
  showNewChatDialog.value = true
  newChatName.value = ''
}

// 确认创建新对话
const confirmNewChat = async () => {
  if (!newChatName.value.trim()) {
    ElMessage.warning('请输入对话名称')
    return
  }

  try {
    const userStore = useUserStore()
    const response = await axios.post('/history_service/list/create',
        {
          name: newChatName.value
        },
        {
          headers: {
            'Authorization': `Bearer ${userStore.accessToken}`
          }
        }
    )

    if (response.data.code === 1) {
      await chatStore.fetchChatLists()
      const newChatId = response.data.data.chat_history_list_id
      showNewChatDialog.value = false
      newChatName.value = ''
      await selectChat(newChatId)
      ElMessage.success('对话创建成功')
    } else {
      throw new Error(response.data.msg || '创建对话失败')
    }
  } catch (error) {
    console.error('Create chat error:', error)
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 可以在这里添加重定向到登录页面的逻辑
      // router.push('/login')
    } else {
      ElMessage.error(error.message || '创建对话失败')
    }
  }
}

// 使用计算属性获取聊天记录
const chatLists = computed(() => chatStore.chatLists)
const chatDetails = computed(() => chatStore.chatDetails.get(currentChatId.value) || [])

// 获取历史对话列表
const fetchChatLists = async () => {
  await chatStore.fetchChatLists()
}

// 获取特定对话的聊天记录
const fetchChatDetails = async (listId) => {
  await chatStore.fetchChatDetails(listId)
  await nextTick()
  scrollToBottom()
}

// 选择对话
const selectChat = async (chatId) => {
  if (!chatId) return

  try {
    currentChatId.value = chatId
    await fetchChatDetails(chatId)
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('Select chat error:', error)
    ElMessage.error('加载对话失败')
  }
}

//删除对话
const deleteChat = async (listId) => {
  try {
    const confirmed = await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (confirmed) {
      const success = await chatStore.deleteChat(listId)
      if (success) {
        ElMessage.success('删除成功')
        if (currentChatId.value === listId) {
          currentChatId.value = null
        }
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete chat error:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理图片上传
const handleImageUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// 移除已选择的图片
const removeImage = () => {
  selectedImage.value = null
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() && !selectedImage.value) {
    ElMessage.warning('请输入消息或选择图片')
    return
  }

  // 添加用户消息
  const userMessage = {
    chat_history_detail_id: Date.now(),
    role: 'user',
    words: userInput.value,
    is_image: !!selectedImage.value,
    image_url: selectedImage.value,
    image_describe: null
  }
  chatStore.addMessage(currentChatId.value, userMessage)

  const messageData = {
    chat_history_list_id: currentChatId.value,
    chat_history_detail: chatDetails.value,
    question: userInput.value,
    image: selectedImage.value
  }

  // 清空输入和图片
  userInput.value = ''
  selectedImage.value = null

  await nextTick()
  scrollToBottom()

  try {
    // 添加空的系统消息
    const systemMessage = {
      chat_history_detail_id: Date.now() + 1,
      role: 'system',
      words: '',
      is_image: false
    }
    chatStore.addMessage(currentChatId.value, systemMessage)

    // 根据数学增强模式选择不同的API端点
    const endpoint = isMathEnhanced.value ? 'http://localhost:5000/math_service/math_chat' : 'http://localhost:5000/chat_service/normal_chat'

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useUserStore().accessToken}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(messageData)
    })

    if (!response.ok) {
      if (response.status === 403) {
        ElMessage.error('Token余额不足，请充值后继续使用')
        // 发生错误时移除最后的系统消息
        const messages = chatStore.chatDetails.get(currentChatId.value) || []
        if (messages.length > 0 && messages[messages.length - 1].role === 'system') {
          messages.pop()
          chatStore.updateChatDetails(currentChatId.value, messages)
        }
        return
      }
      throw new Error(`请求失败: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let currentMessage = ''
    let buffer = ''
    let lastUpdateTime = Date.now()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break

          buffer += data
          const now = Date.now()

          // 使用缓冲区和时间控制来批量更新
          if (buffer.length >= 8 || (now - lastUpdateTime) >= 100) {
            currentMessage += buffer
            chatStore.updateLastMessage(currentChatId.value, currentMessage)
            buffer = ''
            lastUpdateTime = now

            await nextTick()
            scrollToBottom()
            await new Promise(resolve => setTimeout(resolve, 50))
          }
        }
      }
    }

    // 处理剩余的buffer
    if (buffer) {
      currentMessage += buffer
      chatStore.updateLastMessage(currentChatId.value, currentMessage)
      await nextTick()
      scrollToBottom()
    }

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error(error.message || '发送消息失败')
    // 发生错误时移除最后的系统消息
    const messages = chatStore.chatDetails.get(currentChatId.value) || []
    if (messages.length > 0 && messages[messages.length - 1].role === 'system') {
      messages.pop()
      chatStore.updateChatDetails(currentChatId.value, messages)
    }
  }
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 滚动到底部
const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

// 复制消息
const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('复制成功')
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

// 开始编辑消息
const startEdit = (message) => {
  editingMessage.value = message
  editingText.value = message.words
  showEditDialog.value = true
}

// 保存编辑
const saveEdit = async () => {
  try {
    if (!editingText.value.trim()) {
      ElMessage.warning('消息内容不能为空')
      return
    }

    const response = await axios.put(`/history_service/detail/edit/${editingMessage.value.chat_history_detail_id}`, {
      words: editingText.value,
      chat_history_list_id: currentChatId.value
    })

    if (response.data.code === 1) {
      // 更新消息内容
      editingMessage.value.words = editingText.value

      // 发送更新后的消息获取新的AI回复
      userInput.value = editingText.value
      showEditDialog.value = false
      await sendMessage()

      ElMessage.success('更新成功')
    } else {
      throw new Error(response.data.msg || '更新失败')
    }
  } catch (error) {
    console.error('Edit error:', error)
    ElMessage.error(error.response?.data?.msg || error.message || '更新失败')
  }
}

// 删除消息
const deleteMessage = async (detailId) => {
  try {
    const confirmed = await ElMessageBox.confirm('确定要删除这条消息吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (confirmed) {
      const response = await axios.delete(`/history_service/detail/delete/${detailId}`)

      if (response.data.code === 1) {
        // 先添加到已删除消息列表，触发动画
        deletedMessages.value.push(detailId)

        // 等待动画完成后再更新store
        setTimeout(() => {
          const messages = chatStore.chatDetails.get(currentChatId.value) || []
          const filteredMessages = messages.filter(m => m.chat_history_detail_id !== detailId)
          chatStore.updateChatDetails(currentChatId.value, filteredMessages)
        }, 300) // 与动画持续时间匹配

        ElMessage.success('删除成功')
      } else {
        throw new Error(response.data.msg || '删除失败')
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete message error:', error)
      ElMessage.error(error.response?.data?.msg || error.message || '删除失败')
    }
  }
}

onMounted(async () => {
  const userStore = useUserStore()
  if (userStore.accessToken) {
    await chatStore.fetchChatLists()
  } else {
    console.error('用户未登录或token已失效')
    // 可以在这里添加重定向到登录页面的逻辑
  }
})

// 导出必要的方法和变量
defineExpose({
  confirmNewChat,
  selectChat,
  showNewChatDialog,
  newChatName,
  openNewChatDialog,
  deleteChat,
  deleteMessage,
  startEdit,
  saveEdit
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 120px);  /* 修改高度以匹配其他界面 */
  background-color: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin: 60px 20px 20px 120px;  /* 添加外边距 */
}

.history-sidebar {
  width: 280px;
  border-right: 1px solid #eef0f7;
  display: flex;
  flex-direction: column;
}

.history-header {
  padding: 24px;
  border-bottom: 1px solid #eef0f7;
  background: linear-gradient(to right, #f8f9fe, #ffffff);
}

.history-header h2 {
  color: #6c5dd3;
  font-size: 1.5rem;
  margin-bottom: 16px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.history-item:hover {
  background-color: #f8f9fe;
}

.history-item.active {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  color: white;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.2);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 70%;
  animation: message-pop-in 0.3s ease-out;
}

.message-user {
  align-items: flex-end;
}

.message-ai {
  align-items: flex-start;
}

.message-content {
  position: relative;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #f8f9fe;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
  padding: 4px 0;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: rgba(108, 93, 211, 0.1);
  color: #6c5dd3;
}

.message-user .message-content {
  background: linear-gradient(135deg, #6c5dd3, #8e6cff);
  color: white;
}

.message-ai .message-content {
  background: #f8f9fe;
  border: 1px solid #eef0f7;
}

.edit-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #6c5dd3;
  border-radius: 4px;
  outline: none;
  font-size: inherit;
  background: white;
}

.message-text {
  word-break: break-word;
  line-height: 1.5;
}

/* 添加工具提示样式 */
.action-btn {
  position: relative;
}

.action-btn:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  margin-bottom: 4px;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #eef0f7;
}

.new-chat-shortcut-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.new-chat-shortcut {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background-color: #eef1f8;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.new-chat-shortcut:hover {
  background-color: #e4e7f0;
  color: #333;
}

.new-chat-shortcut .btn-icon {
  font-size: 18px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: #ffffff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

textarea {
  flex: 1;
  height: 60px;
  padding: 12px;
  border: 1px solid #eef0f7;
  border-radius: 8px;
  resize: none;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.input-container textarea:focus {
  border-color: #6c5dd3;
  box-shadow: 0 0 0 2px rgba(108, 93, 211, 0.1);
  outline: none;
}

.input-actions {
  display: flex;
  gap: 8px;
}

.upload-btn, .send-btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  color: white;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.upload-btn:hover, .send-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.image-preview {
  margin-top: 12px;
  position: relative;
  display: inline-block;
}

.image-preview img {
  max-height: 100px;
  border-radius: 8px;
}

.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-container {
  margin-bottom: 8px;
}

.image-container img {
  max-width: 100%;
  border-radius: 8px;
}

.image-description {
  margin-top: 4px;
  font-size: 14px;
  color: #666;
}
/* 新增弹窗样式 */
.dialog-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.new-chat-dialog {
  width: 420px;
  height: 240px;
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.name-input {
  width: 100%;
  height: 40px;
  margin: 30px 0;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.confirm-btn {
  width: 120px;
  padding: 12px;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.3s;
  display: flex;
  justify-content: center;
}

.confirm-btn:hover {
  opacity: 0.9;
}

/* 删除按钮样式 */
.delete-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #ff4757;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.history-item {
  position: relative; /* 添加定位 */
  padding-right: 40px; /* 给删除按钮留空间 */
}

/* 添加消息动画相关样式 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 添加删除时的动画效果 */
.message-wrapper.deleting {
  animation: message-fade-out 0.3s ease-out forwards;
}

@keyframes message-fade-out {
  to {
    opacity: 0;
    transform: translateY(-20px);
  }
}

/* 优化编辑弹窗样式 */
.edit-dialog {
  width: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  animation: dialog-pop-in 0.3s ease-out;
}

@keyframes dialog-pop-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.edit-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eef0f7;
}

.edit-dialog-header h3 {
  font-size: 18px;
  color: #1a1a1a;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1a1a1a;
}

.edit-dialog-body {
  padding: 24px;
}

.edit-textarea {
  width: 90%;
  min-height: 180px;
  padding: 16px;
  border: 1px solid #eef0f7;
  border-radius: 12px;
  resize: vertical;
  font-size: 15px;
  line-height: 1.6;
  color: #1a1a1a;
  background: #f8f9fe;
  transition: all 0.3s ease;
}

.edit-textarea:focus {
  outline: none;
  border-color: #6c5dd3;
  background: white;
  box-shadow: 0 0 0 3px rgba(108, 93, 211, 0.1);
}

.textarea-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 4px;
}

.hint {
  font-size: 13px;
  color: #666;
}

.word-count {
  font-size: 13px;
  color: #666;
}

.edit-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #eef0f7;
  background: #f8f9fe;
  border-radius: 0 0 16px 16px;
}

.cancel-btn, .confirm-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  border: 1px solid #eef0f7;
  background: white;
  color: #666;
}

.cancel-btn:hover {
  background: #f8f9fe;
  border-color: #dde0e9;
  color: #1a1a1a;
}

.confirm-btn {
  border: none;
  background: linear-gradient(135deg, #6c5dd3, #8e6cff);
  color: white;
}

.confirm-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.btn-icon {
  font-size: 18px;
}

.dialog-mask {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
}

/* 添加删除按钮的特殊样式 */
.delete-action {
  color: #ff4757;
  transition: all 0.3s ease;
}

.delete-action:hover {
  background: rgba(255, 71, 87, 0.1);
  color: #ff4757;
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
:deep(.message-text) {
  line-height: 1.6;
}

:deep(.message-text p) {
  margin: 0.5em 0;
}

:deep(.message-text code) {
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

:deep(.message-text pre) {
  background-color: #f5f5f5;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

:deep(.message-text blockquote) {
  border-left: 4px solid #6c5dd3;
  margin: 0;
  padding-left: 1em;
  color: #666;
}

:deep(.message-text ul), :deep(.message-text ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.math-enhance-btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: #eef0f7;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
}

.math-enhance-btn:hover {
  background: #e4e7f0;
  color: #333;
}

.math-enhance-btn.active {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.math-enhance-btn.active:hover {
  opacity: 0.9;
}
</style>

