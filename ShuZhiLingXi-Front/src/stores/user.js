import { defineStore } from 'pinia';
import axios from '../utils/axios';

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: null,
    username: null,
    accessToken: null,
    refreshToken: null,
    userAdvice: '',
    tokenBalance: 0,
    profilePicture: '',
    isLoadingAdvice: false
  }),

  actions: {
    setUserInfo(userInfo) {
      this.userId = userInfo.user_id;
      this.username = userInfo.username;
      this.accessToken = userInfo.access_token;
      this.refreshToken = userInfo.refresh_token;
      this.tokenBalance = userInfo.token_balance || 0;
      this.profilePicture = userInfo.profile_picture;
    },

    clearUserInfo() {
      this.userId = null;
      this.username = null;
      this.accessToken = null;
      this.refreshToken = null;
      this.tokenBalance = 0;
      this.profilePicture = '';
      localStorage.removeItem('remember');
    },

    updateAccessToken(newToken) {
      this.accessToken = newToken;
    },

    async fetchUserAdvice() {
      try {
        this.isLoadingAdvice = true;
        const response = await fetch('http://127.0.0.1:5000/auth/user/advice', {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`
          }
        });

        if (!response.ok) {
          throw new Error(`请求失败: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let advice = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') break;
              if (!data.startsWith('[TOKENS:')) {
                advice += data;
                this.userAdvice = advice;
              }
            }
          }
        }

        return advice;
      } catch (error) {
        console.error('获取建议失败:', error);
        throw error;
      } finally {
        this.isLoadingAdvice = false;
      }
    },

    setUserAdvice(advice) {
      this.userAdvice = advice;
    },

    setProfilePicture(url) {
      this.profilePicture = url;
    }
  },

  persist: {
    enabled: true,
    strategies: [
      {
        key: 'user',
        storage: localStorage,
        paths: ['userId', 'username']
      },
      {
        key: 'auth',
        storage: localStorage,
        paths: ['accessToken', 'refreshToken']
      }
    ]
  }
});
