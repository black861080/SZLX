<template>
  <main-layouts>
    <!-- 添加通知组件 -->
    <div v-if="notification.show" class="notification" :class="notification.type">
      {{ notification.message }}
    </div>
    <!-- 添加头栏 -->
    <div class="header">
      <div class="header-left">
        <div class="search-box" @click="handleSearchClick">
          <Icon icon="streamline:magnifying-glass-solid" class="search-icon" />
          <input
            type="text"
            placeholder="搜索笔记、错题..."
            readonly
            class="search-input"
          >
          <div class="search-shortcut">⌘K</div>
        </div>
      </div>
      <div class="header-right">
        <div class="token-balance">
          <div class="token-icon-wrapper">
            <Icon icon="mdi:coin" class="token-icon" />
          </div>
          <div class="token-amount">
            <span class="token-value">{{ formatNumber(userInfo?.token_balance || 0) }}</span>
            <span class="token-label">Token</span>
          </div>
        </div>
        <div class="user-profile" @click="showDropdown = !showDropdown">
          <img :src="userStore.profilePicture || defaultAvatar" alt="用户头像" class="avatar">
          <span class="username">{{ userStore.username }}</span>
          <Icon icon="mdi:chevron-down" class="dropdown-arrow" :class="{ 'rotate': showDropdown }" />
          <!-- 下拉菜单 -->
          <div v-if="showDropdown" class="dropdown-menu">
            <input
              type="file"
              ref="fileInput"
              style="display: none"
              accept="image/*"
              @change="(e) => handleAvatarChange(e.target.files[0])"
            >
            <div class="dropdown-item" @click="triggerFileInput">
              <Icon icon="mdi:account-edit" class="dropdown-icon" />
              修改头像
            </div>
            <div class="dropdown-item" @click="handleLogout">
              <Icon icon="material-symbols:logout" class="dropdown-icon" />
              退出登录
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="home-container">
      <div class="welcome-section">
        <h1>欢迎回来，{{ userStore.username }}</h1>
        <p class="subtitle">今天也要努力学习哦！</p>
      </div>

      <div class="stats-grid">
        <!-- 学习进度卡片 -->
        <div class="stat-card">
          <div class="card-icon">
            <Icon icon="material-symbols:book" />
          </div>
          <div class="card-content">
            <h3>学习章节</h3>
            <div class="number">{{ userInfo?.chapter_count || 0 }}</div>
          </div>
        </div>

        <!-- 笔记统计卡片 -->
        <div class="stat-card">
          <div class="card-icon">
            <Icon icon="material-symbols:note" />
          </div>
          <div class="card-content">
            <h3>笔记总数</h3>
            <div class="number">{{ userInfo?.notes_count || 0 }}</div>
          </div>
        </div>

        <!-- 剩余Token卡片 -->
        <div class="stat-card">
          <div class="card-icon">
            <Icon icon="material-symbols:error" />
          </div>
          <div class="card-content">
            <h3>错题数量</h3>
            <div class="number">{{ formatNumber(userInfo?.mistaken_question_count || 0) }}</div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-container">
        <!-- 笔记质量分布饼图 -->
        <div class="chart-card">
          <h3>笔记质量分布</h3>
          <div ref="notesQualityChart" class="chart"></div>
        </div>

        <!-- 学习进度趋势图 -->
        <div class="chart-card">
          <h3>学习进度趋势</h3>
          <div ref="learningProgressChart" class="chart"></div>
        </div>

      </div>

      <!-- Token消费趋势图 -->
      <div class="chart-card">
        <h3>Token消费趋势</h3>
        <div ref="tokenUsageChart" class="chart"></div>
      </div>

      <!-- 个性化建议区域 -->
      <div class="advice-section">
        <h3>今日建议</h3>
        <div class="advice-content" v-if="userStore.userAdvice">
          {{ userStore.userAdvice }}
        </div>
        <div class="advice-content loading" v-else-if="userStore.isLoadingAdvice">
          正在生成建议...
        </div>
        <div class="advice-content" v-else>
          暂无建议
        </div>
      </div>
    </div>
  </main-layouts>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useUserStore } from '../stores/user';
import axios from '../utils/axios';
import MainLayouts from "../layouts/MainLayouts.vue";
import { Icon } from '@iconify/vue';
import * as echarts from 'echarts';
import { useRouter } from 'vue-router';

const userStore = useUserStore();
const userInfo = ref(null);
const advice = ref('');
const notesQualityChart = ref(null);
const learningProgressChart = ref(null);
const tokenUsageChart = ref(null);
const notesData = ref([]);
let chart1 = null;
let chart2 = null;
let chart3 = null;

// 添加一个会话存储标志
const hasAdviceFetched = ref(sessionStorage.getItem('hasAdviceFetched') === 'true');

const showDropdown = ref(false);
const defaultAvatar = 'https://blackmagic-1329109058.cos.ap-guangzhou.myqcloud.com/chat_images%2F1742457603321.jpg';

const router = useRouter();

// 添加文件输入引用
const fileInput = ref(null);

// 添加触发文件选择的方法
const triggerFileInput = () => {
  fileInput.value.click();
};

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await axios.get(`/auth/user/${userStore.userId}`);
    userInfo.value = response.data;
  } catch (error) {
    console.error('获取用户信息失败:', error);
  }
};

// 获取用户笔记数据
const fetchUserNotes = async () => {
  try {
    const response = await axios.get('/notes_service/notes/weekly');
    notesData.value = response.data || [];
  } catch (error) {
    console.error('获取笔记数据失败:', error);
  }
};

// 获取Token使用数据
const fetchTokenUsage = async () => {
  try {
    const response = await axios.get('auth/token_usage/biweekly');
    return response.data || [];
  } catch (error) {
    console.error('获取Token使用数据失败:', error);
    return [];
  }
};

const fetchAdvice = async () => {
  try {
    advice.value = '';
    await userStore.fetchUserAdvice();
    sessionStorage.setItem('hasAdviceFetched', 'true');
  } catch (error) {
    console.error('获取建议失败:', error);
    advice.value = '获取建议失败，请稍后重试';
  }
};

// 初始化笔记质量分布饼图
const initNotesQualityChart = () => {
  if (!notesQualityChart.value) return;

  chart1 = echarts.init(notesQualityChart.value);
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        type: 'pie',
        radius: '50%',
        data: [
          { value: userInfo.value?.clear_notes_count || 0, name: '清晰笔记' },
          { value: userInfo.value?.vague_notes_count || 0, name: '模糊笔记' },
          { value: userInfo.value?.unclear_notes_count || 0, name: '不清晰笔记' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
  chart1.setOption(option);
};

// 初始化学习进度趋势图
const initLearningProgressChart = () => {
  if (!learningProgressChart.value) return;

  // 获取最近7天的日期
  const last7Days = Array.from({length: 7}, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    return date;
  });

  // 格式化日期为 'MM-DD' 格式
  const formatDate = (date) => {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${month}-${day}`;
  };

  // 统计每天的笔记数量
  const dailyNotesCount = last7Days.map(date => {
    const formattedDate = formatDate(date);
    const count = notesData.value.filter(note => {
      const noteDate = new Date(note.created_at);
      return formatDate(noteDate) === formattedDate;
    }).length;
    return {
      date: formattedDate,
      count: count
    };
  });

  chart2 = echarts.init(learningProgressChart.value);
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c} 条笔记'
    },
    xAxis: {
      type: 'category',
      data: dailyNotesCount.map(item => item.date),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '笔记数量',
      minInterval: 1
    },
    series: [
      {
        data: dailyNotesCount.map(item => item.count),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.2)'
        },
        itemStyle: {
          color: '#6c5dd3'
        }
      }
    ]
  };
  chart2.setOption(option);
};

// 初始化Token使用趋势图
const initTokenUsageChart = (tokenData) => {
  if (!tokenUsageChart.value) return;

  // 修改为获取最近14天的日期
  const last14Days = Array.from({length: 14}, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (13 - i));
    return date;
  });

  const formatDate = (date) => {
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${month}-${day}`;
  };

  const dailyTokenUsage = last14Days.map(date => {
    const formattedDate = formatDate(date);
    const usage = tokenData.filter(item => {
      const itemDate = new Date(item.created_at);
      return formatDate(itemDate) === formattedDate;
    }).reduce((sum, item) => sum + (item.spand || 0), 0);
    return {
      date: formattedDate,
      usage: usage
    };
  });

  chart3 = echarts.init(tokenUsageChart.value);
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c} tokens'
    },
    xAxis: {
      type: 'category',
      data: dailyTokenUsage.map(item => item.date),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: 'Token使用量'
    },
    series: [{
      data: dailyTokenUsage.map(item => item.usage),
      type: 'line',
      smooth: true,
      lineStyle: {
        color: '#6c5dd3'
      },
      itemStyle: {
        color: '#6c5dd3'
      }
    }]
  };
  chart3.setOption(option);
};

// 监听窗口大小变化，调整图表大小
const handleResize = () => {
  chart1?.resize();
  chart2?.resize();
  chart3?.resize();
};

// 添加格式化数字的函数
const formatNumber = (num) => {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + 'B';
  } else if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

// 添加通知状态
const notification = ref({
  show: false,
  message: '',
  type: 'success'
});

// 显示通知的函数
const showNotification = (message, type = 'success') => {
  notification.value = {
    show: true,
    message,
    type
  };

  // 3秒后自动隐藏
  setTimeout(() => {
    notification.value.show = false;
  }, 3000);
};

const handleAvatarChange = async (file) => {
  try {
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      showNotification('头像图片大小不能超过 5MB!', 'error');
      return;
    }

    // 读取图片文件为 base64
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async (e) => {
      try {
        // 只保存 base64 数据部分，去掉 "data:image/jpeg;base64," 这样的前缀
        const base64Data = e.target.result.split(',')[1];

        // 调用后端接口更新头像
        const response = await axios.post('/auth/user/edit/profile_picture', {
          profile_picture: base64Data
        });

        if (response.data.code === 1) {
          // 更新用户状态中的头像
          userStore.setProfilePicture(response.data.profile_picture);

          // 关闭下拉菜单
          showDropdown.value = false;

          // 显示成功消息
          showNotification('头像更新成功！');
        } else {
          throw new Error(response.data.msg || '更新头像失败');
        }
      } catch (error) {
        console.error('更新头像失败:', error);
        showNotification(error.response?.data?.msg || '更新头像失败', 'error');
      }
    };
  } catch (error) {
    console.error('更改头像失败:', error);
    showNotification('更改头像失败: ' + error.message, 'error');
  }
};

const handleLogout = async () => {
  try {
    // 调用后端登出接口
    await axios.post('/auth/logout');

    // 清除用户状态
    userStore.clearUserInfo();

    // 重定向到登录页面
    router.push('/');
  } catch (error) {
    console.error('退出登录失败:', error);
  }
};

// 添加搜索框点击处理函数
const handleSearchClick = () => {
  router.push('/search');
};

onMounted(async () => {
  await fetchUserInfo();
  await fetchUserNotes();
  const tokenData = await fetchTokenUsage();
  initNotesQualityChart();
  initLearningProgressChart();
  initTokenUsageChart(tokenData);
  window.addEventListener('resize', handleResize);

  // 只在没有获取过建议时获取
  if (!hasAdviceFetched.value) {
    await fetchAdvice();
  }
});

// 在组件卸载时不需要清除 hasAdviceFetched，因为我们希望它在会话期间保持
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  chart1?.dispose();
  chart2?.dispose();
  chart3?.dispose();
});
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-section {
  margin-bottom: 30px;
  text-align: center;
}

.welcome-section h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  color: #64748b;
  font-size: 1.2em;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.card-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #6c5dd3, #8e6cff);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon :deep(svg) {
  width: 30px;
  height: 30px;
  color: white;
}

.card-content h3 {
  color: #64748b;
  font-size: 0.9em;
  margin-bottom: 5px;
}

.number {
  font-size: 1.8em;
  font-weight: bold;
  color: #2c3e50;
}

.date {
  font-size: 1.2em;
  color: #2c3e50;
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.token-usage-container {}

.chart-card h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.chart {
  height: 300px;
}

.advice-section {
  margin-top: 30px;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.advice-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.advice-content {
  color: #64748b;
  line-height: 1.6;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
}

.advice-content.loading {
  text-align: center;
  color: #94a3b8;
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }

  .chart {
    height: 250px;
  }
}

.header {
  background-color: white;
  padding: 16px 24px;
  margin: 20px 120px 20px 114px;
  border-radius: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.token-balance {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  background: linear-gradient(135deg, #f8f9fe 0%, #eef0ff 100%);
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: 1px solid rgba(108, 93, 211, 0.1);
  height: 40px;
}

.token-balance:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.1);
}

.token-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6c5dd3 0%, #8e6cff 100%);
  border-radius: 8px;
  padding: 6px;
}

.token-icon {
  color: white;
  width: 16px;
  height: 16px;
}

.token-amount {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.token-value {
  font-size: 1.1em;
  color: #2c3e50;
  line-height: 1;
}

.token-label {
  font-size: 0.7em;
  color: #64748b;
  font-weight: 500;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  position: relative;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.user-profile:hover {
  background-color: #f8f9fe;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.username {
  font-weight: 500;
  color: #2c3e50;
}

.dropdown-arrow {
  color: #64748b;
  transition: transform 0.3s;
}

.dropdown-arrow.rotate {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 8px 0;
  min-width: 160px;
  z-index: 1000;
  margin-top: 8px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  color: #2c3e50;
  transition: background-color 0.3s;
}

.dropdown-item:hover {
  background-color: #f8f9fe;
}

.dropdown-icon {
  width: 20px;
  height: 20px;
  color: #64748b;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .header {
    margin: 20px;
  }
}

@media (max-width: 768px) {
  .username {
    display: none;
  }

  .token-balance {
    padding: 8px;
  }
}

/* 搜索框样式 */
.search-box {
  display: flex;
  align-items: center;
  background-color: #f8f9fe;
  border-radius: 8px;
  padding: 8px 16px;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 300px;
}

.search-box:hover {
  background-color: #f0f2fe;
}

.search-icon {
  color: #64748b;
  width: 20px;
  height: 20px;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
}

.search-input::placeholder {
  color: #94a3b8;
}

.search-shortcut {
  padding: 2px 6px;
  background-color: #e2e8f0;
  border-radius: 4px;
  font-size: 12px;
  color: #64748b;
}

/* 调整头栏布局 */
.header-left {
  flex: 1;
  margin-right: 20px;
}

/* 添加通知样式 */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 8px;
  color: white;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.notification.success {
  background-color: #10B981;
}

.notification.error {
  background-color: #EF4444;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>

