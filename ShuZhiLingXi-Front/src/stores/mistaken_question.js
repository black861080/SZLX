import { defineStore } from 'pinia'
import axios from '../utils/axios'
import { ElMessage } from 'element-plus'

export const useMistakenQuestionStore = defineStore('mistaken_question', {
  state: () => ({
    lists: [],
    questions: [],
    currentList: null,
    statistics: {
      total_count: 0,
      image_count: 0,
      text_count: 0
    }
  }),

  actions: {
    // 获取错题集列表
    async fetchLists() {
      try {
        const response = await axios.get('/mistaken_question_service/list/all')
        if (response.status === 200) {
          this.lists = response.data.data || []
          this.updateStatistics()
        }
      } catch (error) {
        console.error('获取错题集失败:', error)
        throw error
      }
    },

    // 创建错题集
    async createList(listData) {
      try {
        const response = await axios.post('/mistaken_question_service/list/create', listData)
        if (response.status === 200) {
          await this.fetchLists()
          return response.data
        }
      } catch (error) {
        console.error('创建错题集失败:', error)
        ElMessage.error(error.response?.data?.msg || '创建错题集失败')
        throw error
      }
    },

    // 更新错题集
    async updateList(listId, listData) {
      try {
        const response = await axios.put(`/mistaken_question_service/list/edit/${listId}`, listData)
        if (response.status === 200) {
          await this.fetchLists()
          return response.data
        }
      } catch (error) {
        console.error('更新错题集失败:', error)
        ElMessage.error(error.response?.data?.msg || '更新错题集失败')
        throw error
      }
    },

    // 删除错题集
    async deleteList(listId) {
      try {
        const response = await axios.put(`/mistaken_question_service/list/delete/${listId}`)
        if (response.status === 200) {
          this.lists = this.lists.filter(list => list.question_list_id !== listId)
          if (this.currentList?.question_list_id === listId) {
            this.currentList = null
            this.questions = []
          }
          this.updateStatistics()
          return response.data
        }
      } catch (error) {
        console.error('删除错题集失败:', error)
        throw error
      }
    },

    // 获取错题列表
    async fetchQuestions(listId) {
      try {
        const response = await axios.get(`/mistaken_question_service/question/list/${listId}`)
        if (response.status === 200) {
          // 保留原始的 is_favorite 值
          this.questions = (response.data.data || []).map(question => ({
            ...question,
            showAnswer: false,
            showSimilar: false,
            showSimilarAnswer: false,
            generatingAnswer: false,
            generatingSimilar: false,
            generatingSimilarAnswer: false,
            is_favorite: Boolean(question.is_favorite)  // 确保转换为布尔值
          }))
          this.updateStatistics()
        }
      } catch (error) {
        console.error('获取错题失败:', error)
        throw error
      }
    },

    // 创建错题
    async createQuestion(questionData) {
      try {
        const response = await axios.post('/mistaken_question_service/question/create', {
          question_list_id: questionData.question_list_id,
          content: questionData.content,
          image: questionData.image,
          is_image: questionData.is_image,
          answer: questionData.answer
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (response.status === 200) {
          if (this.currentList) {
            // 更新当前错题集的count
            this.currentList.count = (this.currentList.count || 0) + 1

            // 同时更新lists中对应错题集的count
            const listIndex = this.lists.findIndex(list => list.question_list_id === this.currentList.question_list_id)
            if (listIndex !== -1) {
              this.lists[listIndex].count = this.currentList.count
            }

            // 获取最新的问题列表并更新统计信息
            await this.fetchQuestions(this.currentList.question_list_id)
            this.updateStatistics()
          }
          return response.data
        }
      } catch (error) {
        console.error('创建错题失败:', error)
        ElMessage.error(error.response?.data?.msg || '创建错题失败')
        throw error
      }
    },

    // 更新错题
    async updateQuestion(questionId, questionData) {
      try {
        // 构建请求数据
        const requestData = {}

        // 只在有内容时添加 content
        if (questionData.content) {
          requestData.content = questionData.content
        }

        // 只在有图片时添加图片相关数据
        if (questionData.image) {
          requestData.image = questionData.image
          requestData.is_image = true
        } else if ('is_image' in questionData) {
          requestData.is_image = questionData.is_image
        }

        console.log('Updating question with data:', {
          ...requestData,
          image: requestData.image ? '[BASE64_IMAGE]' : null
        })

        const response = await axios.put(
            `/mistaken_question_service/question/edit/${questionId}`,
            requestData
        )

        if (response.status === 200) {
          // 刷新当前问题列表
          if (this.currentList) {
            await this.fetchQuestions(this.currentList.question_list_id)
          }
          return response.data
        }
      } catch (error) {
        console.error('更新错题失败:', error)
        const errorMsg = error.response?.data?.msg || '更新错题失败'
        ElMessage.error(errorMsg)
        throw error
      }
    },

    // 删除错题
    async deleteQuestion(questionId) {
      try {
        const response = await axios.put(`/mistaken_question_service/question/delete/${questionId}`)
        if (response.status === 200) {
          // 更新questions列表
          this.questions = this.questions.filter(question => question.question_id !== questionId)

          // 更新当前错题集的count
          if (this.currentList) {
            this.currentList.count = Math.max(0, this.currentList.count - 1)
            // 同时更新lists中对应错题集的count
            const listIndex = this.lists.findIndex(list => list.question_list_id === this.currentList.question_list_id)
            if (listIndex !== -1) {
              this.lists[listIndex].count = this.currentList.count
            }
          }

          // 更新统计信息
          this.updateStatistics()
          return response.data
        }
      } catch (error) {
        console.error('删除错题失败:', error)
        throw error
      }
    },

    // 设置当前错题集
    setCurrentList(list) {
      this.currentList = list
    },

    // 更新统计信息
    updateStatistics() {
      this.statistics = {
        total_count: this.questions.length,
        image_count: this.questions.filter(q => q.is_image).length,
        favorite_count: this.questions.filter(q => q.is_favorite).length
      }
    },

    // 生成答案
    async generateAnswer(questionId) {
      try {
        const question = this.questions.find(q => q.question_id === questionId)
        if (!question) return

        question.generatingAnswer = true
        question.answer = ''
        let processedLength = 0 // 新增：记录已处理的数据长度

        await axios.post(
            `/mistaken_question_service/question/update_answer/${questionId}`,
            {},
            {
              responseType: 'text',
              onDownloadProgress: (progressEvent) => {
                const rawData = progressEvent.event.target.responseText
                // 只处理新增数据
                const newData = rawData.slice(processedLength)
                processedLength = rawData.length

                const lines = newData.split('\n')
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    const content = line.slice(6).trim()
                    if (content === '[DONE]') return
                    if (content) question.answer += content
                  }
                }
              }
            }
        )
      } catch (error) {
        console.error('生成答案失败:', error)
        ElMessage.error('生成答案失败')
        throw error
      } finally {
        const question = this.questions.find(q => q.question_id === questionId)
        if (question) {
          question.generatingAnswer = false
        }
      }
    },

    // 生成相似题目
    async generateSimilarQuestion(questionId) {
      try {
        const question = this.questions.find(q => q.question_id === questionId)
        question.similar_question = ''
        let processedLength = 0 // 新增

        await axios.post(
            `/mistaken_question_service/question/update_similar_question/${questionId}`,
            {},
            {
              onDownloadProgress: (progressEvent) => {
                const rawData = progressEvent.event.target.responseText
                const newData = rawData.slice(processedLength)
                processedLength = rawData.length

                const lines = newData.split('\n')
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    const content = line.slice(6).trim()
                    if (content === '[DONE]') return
                    if (content) question.similar_question += content
                  }
                }
              }
            }
        )
      } catch (error) {
        console.error('生成相似题目失败:', error)
        ElMessage.error('生成相似题目失败')
        throw error
      } finally {
        const question = this.questions.find(q => q.question_id === questionId)
        if (question) {
          question.generatingSimilar = false
        }
      }
    },

    // 生成相似题目答案
    async generateSimilarAnswer(questionId) {
      try {
        const question = this.questions.find(q => q.question_id === questionId)
        question.similar_answer = ''
        let processedLength = 0 // 新增

        await axios.post(
            `/mistaken_question_service/question/update_similar_answer/${questionId}`,
            {},
            {
              onDownloadProgress: (progressEvent) => {
                const rawData = progressEvent.event.target.responseText
                const newData = rawData.slice(processedLength)
                processedLength = rawData.length

                const lines = newData.split('\n')
                for (const line of lines) {
                  if (line.startsWith('data: ')) {
                    const content = line.slice(6).trim()
                    if (content === '[DONE]') return
                    if (content) question.similar_answer += content
                  }
                }
              }
            }
        )
      } catch (error) {
        console.error('生成相似题目答案失败:', error)
        ElMessage.error('生成相似题目答案失败')
        throw error
      } finally {
        const question = this.questions.find(q => q.question_id === questionId)
        if (question) {
          question.generatingSimilarAnswer = false
        }
      }
    },

    // 切换收藏状态
    async toggleFavorite(questionId) {
      try {
        const response = await axios.put(`/mistaken_question_service/question/toggle_favorite/${questionId}`)
        if (response.status === 200) {
          const question = this.questions.find(q => q.question_id === questionId)
          if (question) {
            question.is_favorite = response.data.data.is_favorite
          }
          return response.data
        }
      } catch (error) {
        console.error('切换收藏状态失败:', error)
        throw error
      }
    }
  }
})
