import { defineStore } from 'pinia'
import axios from '../utils/axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from './user'

export const useChatStore = defineStore('chat', {
  state: () => ({
    chatLists: [],
    chatDetails: new Map(), // 使用 Map 存储不同对话的聊天记录
    lastFetchTimes: new Map(), // 记录每个对话的最后获取时间
    currentChatId: null
  }),

  actions: {
    // 获取历史对话列表
    async fetchChatLists() {
      try {
        const userStore = useUserStore()
        const response = await axios.get('/history_service/list', {
          headers: {
            'Authorization': `Bearer ${userStore.accessToken}`
          }
        })
        if (response.data.code === 1) {
          this.chatLists = response.data.data
        }
      } catch (error) {
        console.error('获取历史对话列表失败:', error)
        throw error
      }
    },

    // 获取特定对话的聊天记录
    async fetchChatDetails(listId) {
      try {
        if (!listId) {
          console.warn('未提供对话ID')
          return
        }
        const response = await axios.get(`/history_service/detail/${listId}`)
        if (response.data.code === 1) {
          this.chatDetails.set(listId, response.data.data)
          this.lastFetchTimes.set(listId, new Date())
        } else {
          throw new Error(response.data.msg || '获取聊天记录失败')
        }
      } catch (error) {
        console.error('获取聊天记录失败:', error)
        throw error
      }
    },

    // 创建新对话
    async createNewChat(name) {
      try {
        const userStore = useUserStore()
        const response = await axios.post('/history_service/list/create',
            {
              name: name || '新对话'
            },
            {
              headers: {
                'Authorization': `Bearer ${userStore.accessToken}`
              }
            }
        )

        if (response.data.code === 1) {
          await this.fetchChatLists()
          return response.data.data.chat_history_list_id
        }
        throw new Error(response.data.msg || '创建对话失败')
      } catch (error) {
        console.error('创建新对话失败:', error)
        throw error
      }
    },

    // 获取缓存的聊天记录，如果过期则重新获取
    async getChatDetails(listId) {
      const CACHE_TIME = 5 * 60 * 1000 // 5分钟缓存
      const lastFetchTime = this.lastFetchTimes.get(listId)

      if (!lastFetchTime || new Date() - lastFetchTime > CACHE_TIME || !this.chatDetails.has(listId)) {
        await this.fetchChatDetails(listId)
      }

      return this.chatDetails.get(listId) || []
    },

    // 更新聊天记录（用于流式响应）
    updateChatDetails(listId, messages) {
      this.chatDetails.set(listId, messages)
      this.lastFetchTimes.set(listId, new Date())
    },

    // 添加新消息到聊天记录
    addMessage(listId, message) {
      const currentMessages = this.chatDetails.get(listId) || []
      currentMessages.push(message)
      this.chatDetails.set(listId, currentMessages)
    },

    // 清除特定对话的缓存
    clearChatCache(listId) {
      this.chatDetails.delete(listId)
      this.lastFetchTimes.delete(listId)
    },

    // 清除所有缓存
    clearAllCache() {
      this.chatDetails.clear()
      this.lastFetchTimes.clear()
    },

    // 添加新的 action 用于流式更新消息
    updateLastMessage(listId, content) {
      const messages = this.chatDetails.get(listId) || []
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1]
        if (lastMessage.role === 'system') {
          lastMessage.words = content
          this.chatDetails.set(listId, messages)
        }
      }
    },
    // 添加删除对话的action
    async deleteChat(listId) {
      try {
        const response = await axios.delete(`/history_service/list/delete/${listId}`)
        if (response.data.code === 1) {
          // 从本地状态移除
          this.chatLists = this.chatLists.filter(chat => chat.chat_history_list_id !== listId)
          this.chatDetails.delete(listId)
          this.lastFetchTimes.delete(listId)

          // 如果删除的是当前对话，重置currentChatId
          if (this.currentChatId === listId) {
            this.currentChatId = null
          }
        }
        return response.data.code === 1
      } catch (error) {
        console.error('删除对话失败:', error)
        throw error
      }
    }
  }
})
