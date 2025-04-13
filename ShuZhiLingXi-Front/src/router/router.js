import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import Register from '../components/Register.vue';
import Home from "../components/Home.vue";
import Plan from '../components/Plan.vue';
import Search from '../components/Search.vue';
import Chat from '../components/Chat.vue';
import Note from '../components/Note.vue';
import MistakenQuestion from '../components/MistakenQuestion.vue';
import { useUserStore } from '../stores/user';
import axios from '../utils/axios';

const routes = [
    {
        path: '/',
        component: Login
    },
    {
        path: '/Register',
        component: Register
    },
    {
        path: '/home',
        component: Home
    },
    {
        path: '/plan',
        component: Plan
    },
    {
        path: '/search',
        component: Search
    },
    {
        path: '/chat',
        component: Chat
    },
    {
        path: '/note',
        component: Note
    },
    {
        path: '/question',
        component: MistakenQuestion
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore();
    
    // 如果访问的是登录页面
    if (to.path === '/') {
        const remember = localStorage.getItem('remember') === 'true';
        const accessToken = userStore.accessToken;
        
        if (remember && accessToken) {
            try {
                // 验证令牌
                const response = await axios.get('/auth/verify-token', {
                    headers: {
                        Authorization: `Bearer ${accessToken}`
                    }
                });
                
                if (response.data.valid) {
                    // 令牌有效，直接跳转到首页
                    return next('/home');
                }
            } catch (error) {
                // 令牌验证失败，尝试使用刷新令牌
                try {
                    const refreshResponse = await axios.post('/auth/refresh', {}, {
                        headers: {
                            Authorization: `Bearer ${userStore.refreshToken}`
                        }
                    });
                    
                    if (refreshResponse.data.access_token) {
                        userStore.updateAccessToken(refreshResponse.data.access_token);
                        return next('/home');
                    }
                } catch (refreshError) {
                    // 刷新失败，清除存储的信息
                    localStorage.removeItem('auth');
                    localStorage.removeItem('remember');
                    userStore.clearUserInfo();
                }
            }
        }
    }
    
    // 对于需要登录的页面进行验证
    const publicPages = ['/', '/register'];
    const authRequired = !publicPages.includes(to.path);
    
    if (authRequired && !userStore.accessToken) {
        return next('/');
    }
    
    next();
});

export default router
