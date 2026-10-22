import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'

import App from './App.vue'
import { useTheme } from './composables/useTheme'
import router from './router'

import '@/styles/themes.css'
import '@/styles/main.css'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
app.use(router)

// 把持久化的主题应用一次，补齐 index.html 内联脚本之后的兜底
useTheme().initTheme()

app.mount('#app')
