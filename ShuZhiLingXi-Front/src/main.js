import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';
import App from './App.vue';
import router from './router/router.js';
import axios from './utils/axios';
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);

const app = createApp(App);
app.use(pinia);
app.use(router);
app.use(ElementPlus)
app.config.globalProperties.$axios = axios;
app.mount('#app');
