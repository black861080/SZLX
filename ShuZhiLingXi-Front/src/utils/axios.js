import axios from 'axios';
import { useUserStore } from '../stores/user';

const instance = axios.create({
  baseURL: 'http://127.0.0.1:5000',
  timeout: 30000
});

instance.interceptors.request.use(
  config => {
    const userStore = useUserStore();
    if (userStore.accessToken) {
      config.headers.Authorization = `Bearer ${userStore.accessToken}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

instance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    const userStore = useUserStore();
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const response = await axios.post('http://127.0.0.1:5000/auth/refresh', {}, {
          headers: { 'Authorization': `Bearer ${userStore.refreshToken}` }
        });

        if (response.data.access_token) {
          userStore.updateAccessToken(response.data.access_token);
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return instance(originalRequest);
        }
      } catch (refreshError) {
        // 只有在记住登录为false时才清除用户信息
        if (localStorage.getItem('remember') !== 'true') {
          userStore.clearUserInfo();
          window.location.href = '/';
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
