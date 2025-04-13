<template>
  <div class="page-container">
    <div class="form-container">

      <div class="form-header">
        <h2>创建账号</h2>
        <p class="subtitle">请填写以下信息完成注册</p>
      </div>

      <form @submit.prevent="register" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <i class="fas fa-user"></i>
            <input
              type="text"
              v-model="username"
              required
              placeholder="请输入用户名（不超过10个字符）"
              maxlength="10"
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

        <button type="submit" class="btn">
          <span>注册</span>
          <i class="fas fa-arrow-right"></i>
        </button>
      </form>

      <div class="form-footer">
        <router-link to="/" class="register-link">
          <span>已有账号？</span>
          <span class="highlight">立即登录</span>
        </router-link>
      </div>
    </div>

    <div v-if="showModal" class="modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <p>{{ modalMessage }}</p>
        <button @click="handleModalConfirm" class="btn">确定</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from '../utils/axios';

export default {
  data() {
    return {
      username: '',
      password: '',
      showModal: false,
      modalMessage: '',
      registrationSuccess: false
    };
  },
  methods: {
    async register() {
      try {
        const response = await axios.post('/register_service/register', {
          username: this.username,
          password: this.password,
        });

        this.modalMessage = response.data.message;
        this.registrationSuccess = true;
        this.showModal = true;

      } catch (error) {
        this.modalMessage = error.response?.data?.message || '注册失败，请稍后重试';
        this.registrationSuccess = false;
        this.showModal = true;
      }
    },
    closeModal() {
      this.showModal = false;
    },
    handleModalConfirm() {
      this.showModal = false;
      if (this.registrationSuccess) {
        this.$router.push('/');
      }
    }
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

.register-form {
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

.input-wrapper i {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 16px;
  transition: all 0.3s ease;
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

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(108, 93, 211, 0.2);
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

.modal {
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

.modal-content {
  background: white;
  width: 380px;
  padding: 32px;
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(108, 93, 211, 0.1);
}

.modal-content .btn {
  width: auto;
  min-width: 120px;
  margin: 24px auto 0;
  padding: 12px 24px;
}

.input-wrapper:focus-within i {
  color: #6c5dd3;
}

.custom-input:hover {
  border-color: #8674ff;
}
</style>
