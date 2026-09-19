import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Chat from '../views/Chat.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Login',
      component: Login
    },
    {
      path: '/chat',
      name: 'Chat',
      component: Chat,
      beforeEnter: (to, from, next) => {
        const userInfo = localStorage.getItem('userInfo')
        if (userInfo) {
          next()
        } else {
          next('/')
        }
      }
    }
  ]
})

export default router
