<template>
  <div class="page-container">
    <div class="form-container">
      <div class="form-header">
        <h2>欢迎回来</h2>
        <p class="subtitle">很高兴再次见到您</p>
      </div>

      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <i class="fas fa-user"></i>
            <input
              type="text"
              v-model="username"
              required
              placeholder="请输入用户名"
              class="custom-input"
            />
            <span class="input-focus-border"></span>
          </div>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <i class="fas fa-lock"></i>
            <input
              type="password"
              v-model="password"
              required
              placeholder="请输入密码"
              class="custom-input"
            />
            <span class="input-focus-border"></span>
          </div>
        </div>

        <div class="form-group">
          <label for="rememberMe">七天内免密登录</label>
          <input
            type="checkbox"
            v-model="rememberMe"
            class="custom-checkbox"
          />
        </div>

        <button type="submit" class="btn">
          <span>登录</span>
          <i class="fas fa-arrow-right"></i>
        </button>
      </form>

      <div class="form-footer">
        <router-link to="/register" class="register-link">
          <span>没有账号？</span>
          <span class="highlight">立即注册</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../utils/axios';
import { useUserStore } from '../stores/user';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const username = ref('');
    const password = ref('');
    const rememberMe = ref(false);
    const showModal = ref(false);
    const modalMessage = ref('');
    const router = useRouter();
    const userStore = useUserStore();

    const login = async () => {
      try {
        const response = await axios.post('/auth/login', {
          username: username.value,
          password: password.value,
          remember: rememberMe.value
        });

        if (response.data.access_token) {
          // 存储用户信息
          userStore.setUserInfo({
            user_id: response.data.user_id,
            username: response.data.username,
            access_token: response.data.access_token,
            refresh_token: response.data.refresh_token,
            token_balance: response.data.token_balance,
            profile_picture: response.data.profile_picture
          });

          // 存储记住登录状态
          localStorage.setItem('remember', rememberMe.value.toString());

          router.push('/home');
        }
      } catch (error) {
        console.error('Login failed:', error);
        modalMessage.value = error.response?.data?.message || '登录失败，请稍后重试';
        showModal.value = true;
      }
    };

    return {
      username,
      password,
      rememberMe,
      showModal,
      modalMessage,
      login
    };
  }
};
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f6f5ff 0%, #f1efff 100%);
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.form-container {
  width: 380px;
  padding: 32px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(108, 93, 211, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.form-header {
  width: 100%;
  text-align: center;
  margin-bottom: 32px;
}

.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.form-group {
  width: 85%;
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #4b5563;
  font-weight: 500;
  font-size: 14px;
}

.input-wrapper {
  width: 260px;
}

.btn {
  width: 50%;
  padding: 14px;
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  letter-spacing: 0.5px;
  margin: 32px auto 0;
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.15);
}

.form-footer {
  width: 100%;
  margin-top: 32px;
  text-align: center;
  position: relative;
}

.form-footer::before {
  content: '';
  position: absolute;
  top: -16px;
  left: 50%;
  transform: translateX(-50%);
  width: 85%;
  height: 1px;
  background: linear-gradient(90deg,
    transparent,
    rgba(108, 93, 211, 0.1),
    transparent
  );
}

.register-link {
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}

.register-link:hover {
  color: #6c5dd3;
}

.highlight {
  color: #6c5dd3;
  font-weight: 600;
  position: relative;
  transition: all 0.3s ease;
}

.highlight::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.register-link:hover .highlight::after {
  transform: scaleX(1);
}

.custom-input {
  width: 100%;
  padding: 14px 15px 14px 45px;
  border: 2px solid #eef0f7;
  border-radius: 12px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: #f8f9fe;
}

.custom-input:focus {
  border-color: #6c5dd3;
  background: white;
  box-shadow: 0 0 0 4px rgba(108, 93, 211, 0.08);
}

/* 添加输入框图标动画 */
.input-wrapper i {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 16px;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within i {
  color: #6c5dd3;
  transform: translateY(-50%) scale(1.1);
}

.form-header h2 {
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-size: 32px;
  margin-bottom: 12px;
  font-weight: 700;
}

.subtitle {
  color: #94a3b8;
  font-size: 16px;
}

.input-focus-border {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #84fab0, #8fd3f4);
  transition: width 0.3s ease;
}

.btn i {
  transition: transform 0.3s ease;
}

.btn:hover i {
  transform: translateX(5px);
}

/* Modal 样式优化 */
.modal {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 20px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(108, 93, 211, 0.1);
  width: auto;
  min-width: 320px;
  position: relative;
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 添加输入框聚焦时图标颜色变化 */
.input-wrapper:focus-within i {
  color: #6c5dd3;
}

/* 添加输入框hover效果 */
.custom-input:hover {
  border-color: #8674ff;
}
</style>
