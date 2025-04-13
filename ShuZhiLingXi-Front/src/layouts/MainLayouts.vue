<template>
  <div class="app-container">
    <!-- 左侧菜单 -->
    <div class="sidebar" :class="{ expanded: isExpanded }" @mouseenter="isExpanded = true" @mouseleave="isExpanded = false">
      <div class="logo">
        <img src="https://blackmagic-1329109058.cos.ap-guangzhou.myqcloud.com/chat_images%2Fcf2a85d4-35f1-45f6-b1fd-05ce60e0b69a.jpg">
        <span class="logo-text">数智灵犀</span>
      </div>

      <!-- 主要菜单项 -->
      <div class="menu-section">
        <ul class="menu-list">
          <li
            v-for="item in menuItems"
            :key="item.id"
            class="menu-item"
            :class="{ active: currentPath === item.path }"
            @click="handleMenuClick(item)"
          >
            <Icon :icon="item.icon" class="menu-icon" />
            <span class="menu-text">{{ item.name }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import axios from '../utils/axios'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const currentPath = computed(() => route.path)
const showDropdown = ref(false)

const menuItems = ref([
  { id: 1, name: '主页', path: '/home', icon: 'material-symbols:home' },
  { id: 2, name: '错题', path: '/question', icon: 'material-symbols:assignment-late' },
  { id: 3, name: '笔记', path: '/note', icon: 'material-symbols:note' },
  { id: 4, name: '会话', path: '/chat', icon: 'material-symbols:chat' },
  { id: 5, name: '查询', path: '/search', icon: 'streamline:magnifying-glass-solid' },
  { id: 6, name: '计划', path: '/plan', icon: 'material-symbols:calendar-month' },

])

const handleMenuClick = (item) => {
  router.push(item.path)
}

const isExpanded = ref(true)

onMounted(() => {
  setTimeout(() => {
    const sidebar = document.querySelector('.sidebar')
    if (sidebar && !sidebar.matches(':hover')) {
      isExpanded.value = false
    }
  }, 400)
})

const defaultAvatar = 'https://blackmagic-1329109058.cos.ap-guangzhou.myqcloud.com/chat_images%2F1742457603321.jpg'

// 格式化数字函数
const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + 'B'
  } else if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

// 获取当前页面标题
const getCurrentPageTitle = () => {
  const path = route.path
  const item = menuItems.value.find(item => item.path === path)
  return item ? item.name : '首页'
}

const handleChangeAvatar = async () => {
  try {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'

    input.onchange = async (e) => {
      const file = e.target.files[0]
      if (file) {
        // 将文件转换为base64
        const reader = new FileReader()
        reader.onload = async (e) => {
          const base64Image = e.target.result
          try {
            const response = await axios.post('/auth/user/edit/profile_picture', {
              profile_picture: base64Image
            })
            if (response.data.code === 1) {
              userStore.updateProfilePicture(response.data.profile_picture)
              ElMessage.success('头像更新成功')
            } else {
              ElMessage.error('头像更新失败')
            }
          } catch (error) {
            console.error('更新头像失败:', error)
            ElMessage.error('更新头像失败')
          }
        }
        reader.readAsDataURL(file)
      }
    }
    input.click()
  } catch (error) {
    console.error('选择头像失败:', error)
    ElMessage.error('选择头像失败')
  }
}

const handleLogout = async () => {
  try {
    await axios.post('/auth/logout')
    userStore.clearUserInfo()
    router.push('/')
    ElMessage.success('退出登录成功')
  } catch (error) {
    console.error('退出登录失败:', error)
    ElMessage.error('退出登录失败')
  }
}
</script>

<style scoped>
.app-container {
  position: relative;
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 80px;
  background: linear-gradient(180deg, #ffffff 0%, #f8f9fe 100%);
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease-in-out;
  overflow: hidden;
  z-index: 100;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.05);
}

.sidebar.expanded {
  width: 280px;
}

.logo {
  display: flex;
  align-items: center;
  padding: 10px 0;
  margin-top: 10%;
  margin-bottom: 30px;
  position: relative;
  height: 40px;
  width: 100%;
}

.logo img {
  width: 40px;
  height: 40px;
  object-fit: contain;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.15);
}

.sidebar.expanded .logo img {
  left: 0;
  transform: translateX(0);
}

.logo-text {
  font-size: 24px;
  position: absolute;
  left: 50px;
  font-family: "Microsoft YaHei", sans-serif;
  font-weight: 600;
  background: linear-gradient(135deg, #6c5dd3 0%, #8e6cff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
  opacity: 0;
  transform: translateX(-20px);
  transition: all 0.3s ease-in-out;
  pointer-events: none;
}

.sidebar.expanded .logo-text {
  opacity: 1;
  transform: translateX(0);
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
  margin-top: 20px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin: 8px 0;
  cursor: pointer;
  border-radius: 12px;
  color: #666;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 24px;
  position: relative;
  width: 100%;
}

.menu-item:hover {
  background-color: rgba(108, 93, 211, 0.08);
  transform: translateX(4px);
  color: #6c5dd3;
}

.menu-item.active {
  background: linear-gradient(135deg, #6c5dd3 0%, #8e6cff 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.menu-item.active .menu-icon {
  color: white;
}

.menu-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  position: absolute;
  left: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: inherit;
}

.menu-item:hover .menu-icon {
  transform: scale(1.1);
}

.menu-text {
  font-size: 16px;
  white-space: nowrap;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: absolute;
  left: 52px;
  font-weight: 500;
  color: inherit;
}

.sidebar.expanded .menu-text {
  opacity: 1;
}

.main-content {
  min-height: 100vh;
  padding: 0;
  background-color: #F6F5FF;
  margin-left: 80px;
  overflow-y: auto;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
