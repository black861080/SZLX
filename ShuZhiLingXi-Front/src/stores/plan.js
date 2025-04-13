import { defineStore } from 'pinia'
import axios from '../utils/axios'  // 使用配置了JWT的axios实例
import { ElMessage } from 'element-plus'
import { useUserStore } from './user'

export const usePlanStore = defineStore('plan', {
  state: () => ({
    plans: [],
    lastFetchTime: null,
    aiAdvice: '',
    isLoadingAdvice: false,
    hasExistingAdvice: false
  }),

  actions: {
    async fetchPlans() {
      try {
        const response = await axios.get('/plan_service/plans')  // 修改这一行
        this.plans = response.data.plans
        this.lastFetchTime = new Date()
      } catch (error) {
        console.error('获取计划失败:', error)
        throw error
      }
    },

    // 如果数据太旧才重新获取
    async getPlans() {
      const CACHE_TIME = 5 * 60 * 1000 // 5分钟缓存
      if (!this.lastFetchTime || new Date() - this.lastFetchTime > CACHE_TIME) {
        await this.fetchPlans()
      }
      return this.plans
    },

    async createPlan(planData) {
      try {
        const response = await axios.post('/plan_service/plans', planData)  // 修改这一行
        await this.fetchPlans()
        return response.data
      } catch (error) {
        console.error('创建计划失败:', error)
        throw error
      }
    },

    async updatePlan(planId, planData) {
      try {
        console.log('Updating plan:', planId, planData) // 添加日志
        const response = await axios.put(`/plan_service/plans/${planId}`, planData)
        await this.fetchPlans()
        return response.data
      } catch (error) {
        console.error('更新计划失败:', error)
        ElMessage.error(error.response?.data?.message || '更新计划失败')
        throw error
      }
    },

    async deletePlan(planId) {
      try {
        console.log('Deleting plan:', planId) // 添加日志
        const response = await axios.delete(`/plan_service/plans/${planId}`)
        await this.fetchPlans()
        return response.data
      } catch (error) {
        console.error('删除计划失败:', error)
        ElMessage.error(error.response?.data?.message || '删除计划失败')
        throw error
      }
    },

    async getExistingAdvice() {
      try {
        const response = await axios.get('/plan_service/plans/ai_advice/get')
        return response.data
      } catch (error) {
        if (error.response?.status === 404) {
          return null
        }
        throw error
      }
    },

    async getAIAdvice(callback) {
      try {
        this.isLoadingAdvice = true
        this.aiAdvice = ''
        
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
            throw new Error('Token余额不足，请充值后继续使用')
          }
          throw new Error(`请求失败: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let currentAdvice = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              if (data === '[DONE]') break

              currentAdvice += data
              // 更新store状态
              this.aiAdvice = currentAdvice
              
              // 触发回调更新UI
              if (typeof callback === 'function') {
                callback(currentAdvice)
              }
            }
          }
        }
        
        return this.aiAdvice
      } catch (error) {
        console.error('获取AI建议失败:', error)
        throw error
      } finally {
        this.isLoadingAdvice = false
      }
    },

    updateAdvice(advice) {
      this.aiAdvice = advice
    }
  }
})
