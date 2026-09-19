<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-area">
        <div class="logo-icon">🤖</div>
        <h1 class="title">小智 · RAG Agent</h1>
        <p class="subtitle">你的AI数据分析伙伴 ✨</p>
      </div>
      
      <div class="form">
        <div class="form-item">
          <input 
            v-model="email" 
            type="email" 
            placeholder="请输入邮箱地址"
            class="input"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="form-item code-item">
          <input 
            v-model="code" 
            type="text" 
            placeholder="验证码"
            class="input code-input"
            maxlength="6"
            @keyup.enter="handleLogin"
          />
          <button 
            class="code-btn" 
            :disabled="countdown > 0 || !email"
            @click="sendCode"
          >
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </div>
        
        <button 
          class="login-btn" 
          :disabled="!email || !code || loading"
          @click="handleLogin"
        >
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </div>
      
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const code = ref('')
const countdown = ref(0)
const loading = ref(false)
const error = ref('')

let countdownTimer = null

async function sendCode() {
  if (countdown.value > 0 || !email.value) return
  
  try {
    const response = await fetch('/api/send_code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value })
    })
    
    const data = await response.json()
    
    if (data.code === 200) {
      countdown.value = 60
      startCountdown()
    } else {
      error.value = data.msg || '发送失败'
    }
  } catch (e) {
    error.value = '网络错误，请检查后端是否启动'
    console.error('sendCode error:', e)
  }
}

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      clearInterval(countdownTimer)
    }
  }, 1000)
}

async function handleLogin() {
  if (!email.value || !code.value || loading.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, code: code.value })
    })
    
    const data = await response.json()
    
    if (data.code === 200) {
      // 保存完整用户信息
      const userData = data.data || {}
      const userInfo = {
        email: userData.email || email.value,
        name: userData.name || email.value.split('@')[0],
        department: userData.department || '',
        phone: userData.phone || '',
        avatar: userData.avatar || '',
        preferences: userData.preferences || { detail_level: 'normal', default_chart_type: 'bar', theme: 'light' },
        loginTime: Date.now()
      }
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
      router.push('/chat')
    } else {
      error.value = data.msg || '登录失败'
    }
  } catch (e) {
    error.value = '网络错误，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 48px 40px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.logo-area {
  text-align: center;
  margin-bottom: 36px;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  color: #999;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  width: 100%;
}

.code-item {
  display: flex;
  gap: 12px;
}

.input {
  width: 100%;
  padding: 14px 16px;
  font-size: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  outline: none;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.code-input {
  flex: 1;
}

.code-btn {
  padding: 0 16px;
  font-size: 14px;
  color: #667eea;
  background: #f0f0ff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
}

.code-btn:hover:not(:disabled) {
  background: #e0e0ff;
}

.code-btn:disabled {
  color: #ccc;
  background: #f5f5f5;
  cursor: not-allowed;
}

.login-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error {
  color: #e74c3c;
  font-size: 14px;
  text-align: center;
  margin-top: 12px;
}
</style>
