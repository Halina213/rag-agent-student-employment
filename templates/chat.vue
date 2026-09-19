<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="user-card">
        <div class="user-avatar">{{ userName.charAt(0) }}</div>
        <div v-if="!sidebarCollapsed">
          <div class="user-name">{{ userName }}</div>
          <div class="user-dept">{{ userDept || '同学' }}</div>
        </div>
        <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '›' : '‹' }}
        </button>
      </div>

      <button class="new-chat-btn" @click="newChat">
        ✨ 开始新对话
      </button>

      <div class="session-list">
        <div class="session-title">💬 历史会话</div>
        <div v-if="sessions.length === 0" class="session-empty">还没有聊天记录哦～</div>
        <div
          v-for="session in sessions"
          :key="session.session_id"
          class="session-item"
          :class="{ active: currentSessionId === session.session_id }"
          @click="loadSession(session.session_id)"
        >
          📝 {{ formatSessionTime(session.last_active) }}
        </div>
      </div>

      <div class="sidebar-footer">
        <button class="settings-btn" @click="showSettings = true">⚙️ 偏好设置</button>
        <button class="logout-btn" @click="handleLogout">👋 退出登录</button>
      </div>
    </div>

    <!-- 主区域 -->
    <div class="main-area">
      <div class="header">
        <div class="header-left">
          <span class="bot-mascot">🤖</span>
          <div>
            <h1 class="title">小智 · 数据分析助手</h1>
            <span class="bot-status">✨ 在线 · 随时为你服务</span>
          </div>
        </div>
        <div class="user-greeting">{{ greetingText }}</div>
      </div>

      <!-- 消息区 -->
      <div class="messages" ref="messagesRef">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <div class="mascot-bounce">🤖</div>
          <div class="welcome-title">{{ welcomeText }}</div>
          <div class="welcome-sub">{{ welcomeSub }}</div>
          <div class="suggestions">
            <div class="suggestion" @click="quickAsk('📊 就业率分析')">📊 就业率分析</div>
            <div class="suggestion" @click="quickAsk('📈 实习vs就业')">📈 实习vs就业</div>
            <div class="suggestion" @click="quickAsk('🔍 数据查询')">🔍 数据查询</div>
            <div class="suggestion" @click="quickAsk('🎓 我的学院')">🎓 我的学院</div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, index) in messages"
          :key="msg._id || index"
          class="message-wrapper"
          :class="msg.role"
        >
          <div class="message-avatar" :class="{ 'ai-avatar': msg.role === 'ai' }">
            {{ msg.role === 'user' ? userName.charAt(0) : '🤖' }}
          </div>
          <div class="message-content" :class="msg.role">
            <div
              v-if="msg.role === 'ai' && !msg.streaming"
              class="markdown-body"
              v-html="renderMarkdown(msg.content)"
            ></div>
            <div v-else-if="msg.role === 'ai' && msg.streaming" class="typing">
              <span class="typing-text">{{ typingText }}</span>
              <div class="typing-dots">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
            </div>
            <template v-else>{{ msg.content }}</template>
            <div
              v-if="msg.chartOption"
              class="chart-container"
              :id="'chart-' + (msg._id || index)"
            ></div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <button class="upload-btn" @click="triggerUpload" :disabled="isUploading">
          {{ isUploading ? '⏳' : '📎' }}
        </button>
        <input
          class="input"
          v-model="inputText"
          :placeholder="inputPlaceholder"
          @keyup.enter="sendMessage"
          :disabled="isTyping"
        />
        <button class="send-btn" @click="sendMessage" :disabled="isTyping || !inputText.trim()">
          🚀 发送
        </button>
      </div>
      <input type="file" ref="fileInputRef" style="display:none" @change="handleFileUpload" accept=".csv,.xlsx,.xls" />
    </div>

    <!-- 偏好设置弹窗 -->
    <div v-if="showSettings" class="modal-overlay" @click.self="showSettings = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>⚙️ 个性化设置</h3>
          <button class="modal-close" @click="showSettings = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="setting-item">
            <label>📝 回答详细程度</label>
            <div class="setting-options">
              <button
                v-for="opt in detailOptions"
                :key="opt.value"
                class="setting-option"
                :class="{ active: settings.detail_level === opt.value }"
                @click="settings.detail_level = opt.value"
              >{{ opt.label }}</button>
            </div>
          </div>
          <div class="setting-item">
            <label>📊 默认图表类型</label>
            <div class="setting-options">
              <button
                v-for="opt in chartOptions"
                :key="opt.value"
                class="setting-option"
                :class="{ active: settings.default_chart_type === opt.value }"
                @click="settings.default_chart_type = opt.value"
              >{{ opt.label }}</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="save-btn" @click="saveSettings">✨ 保存设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { fetchSSE } from '../utils/sse.js'
import * as echarts from 'echarts'

marked.setOptions({ breaks: true, gfm: true })

const router = useRouter()
const messagesRef = ref(null)
const messages = ref([])
const inputText = ref('')
const isTyping = ref(false)
const isUploading = ref(false)
const uploadedFile = ref(null)
const fileInputRef = ref(null)
const sidebarCollapsed = ref(false)
const showSettings = ref(false)
const sessions = ref([])
const currentSessionId = ref(null)

let userInfo = null
let currentController = null
let msgIdCounter = 0

function makeMsgId() { return 'msg-' + (++msgIdCounter) }

let chartInstances = {}
let typingTimer = null

const settings = ref({
  detail_level: 'normal',
  default_chart_type: 'bar',
  theme: 'light'
})

const detailOptions = [
  { value: 'simple', label: '🌸 简洁' },
  { value: 'normal', label: '🌿 标准' },
  { value: 'detailed', label: '🌳 详细' }
]

const chartOptions = [
  { value: 'bar', label: '📊 柱状图' },
  { value: 'line', label: '📈 折线图' },
  { value: 'pie', label: '🥧 饼图' },
  { value: 'scatter', label: '⚬ 散点图' }
]

const themeOptions = [
  { value: 'light', label: '☀️ 浅色' },
  { value: 'dark', label: '🌙 深色' }
]

// 可爱的打字提示文本
const typingPhrases = ['小智正在思考中', '正在查询数据', '努力分析中', '马上就好啦', '让小智想想']
const typingText = ref('小智正在思考中')

const userName = computed(() => userInfo?.name || '同学')
const userDept = computed(() => userInfo?.department || '')

const greetingText = computed(() => {
  const hour = new Date().getHours()
  let emoji = '☀️'
  let greet = '你好'
  if (hour < 6) { greet = '夜深了'; emoji = '🌙' }
  else if (hour < 9) { greet = '早安呀'; emoji = '🌅' }
  else if (hour < 12) { greet = '上午好呀'; emoji = '☀️' }
  else if (hour < 14) { greet = '中午好呀'; emoji = '🌤️' }
  else if (hour < 18) { greet = '下午好呀'; emoji = '🌞' }
  else if (hour < 22) { greet = '晚上好呀'; emoji = '🌆' }
  else { greet = '夜深了'; emoji = '🌙' }
  return `${emoji} ${greet}，${userName.value}～`
})

const welcomeText = computed(() => {
  const greetings = [
    `嗨 ${userName.value}！我是小智 🤖`,
    `${userName.value}，你来啦！✨`,
    `欢迎回来，${userName.value}！🎉`
  ]
  return greetings[Math.floor(Date.now() / 60000) % greetings.length]
})

const welcomeSub = computed(() => {
  const subs = [
    '我可以帮你分析数据、画图表、回答问题，快来试试吧～ 💪',
    '有什么数据想了解的？尽管问我！🌟',
    '今天想探索什么数据呢？我随时待命～ 🚀'
  ]
  if (userDept.value) {
    return `作为${userDept.value}的一员，要不要先看看你们学院的就业数据？🌟`
  }
  return subs[Math.floor(Date.now() / 60000) % subs.length]
})

const inputPlaceholder = computed(() => {
  const placeholders = [
    '问问小智吧～',
    '想了解什么数据呢？',
    '输入你的问题～',
    '小智等你提问呢～'
  ]
  return placeholders[Math.floor(Date.now() / 30000) % placeholders.length]
})

onMounted(() => {
  const stored = localStorage.getItem('userInfo')
  if (stored) {
    userInfo = JSON.parse(stored)
    settings.value = { ...settings.value, ...(userInfo.preferences || {}) }
  }
  loadSessions()
})

onBeforeUnmount(() => {
  Object.values(chartInstances).forEach(chart => chart?.dispose())
  if (typingTimer) clearInterval(typingTimer)
})

function renderMarkdown(text) {
  if (!text) return ''
  return marked(text)
}

function escapeHtml(text) {
  if (!text) return ''
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
}

function renderChart(msgId, chartOption) {
  nextTick(() => {
    const el = document.getElementById('chart-' + msgId)
    if (!el || !chartOption) return
    if (chartInstances[msgId]) chartInstances[msgId].dispose()
    const chart = echarts.init(el)
    try { chart.setOption(chartOption) } catch (e) { console.error('ECharts error:', e) }
    chartInstances[msgId] = chart
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => {
        if (chartInstances[msgId]) chartInstances[msgId].resize()
      })
      ro.observe(el)
    }
  })
}

function rerenderAllCharts() {
  nextTick(() => {
    messages.value.forEach(msg => {
      if (msg.chartOption && msg._id) {
        const el = document.getElementById('chart-' + msg._id)
        if (el) renderChart(msg._id, msg.chartOption)
      }
    })
  })
}

function tryParseChartOption(text) {
  if (!text) return null
  let cleaned = text.trim()
  if (cleaned.includes('{{')) {
    const fixed = cleaned.replace(/\{\{/g, '{').replace(/\}\}/g, '}')
    try { JSON.parse(fixed); cleaned = fixed } catch(e) {}
  }
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```\w*\n?/, '')
    if (cleaned.endsWith('```')) cleaned = cleaned.slice(0, -3).trim()
  }
  try {
    const obj = JSON.parse(cleaned)
    if (obj && (obj.series || obj.xAxis || obj.yAxis)) return obj
    if (obj?.chart && (obj.chart.series || obj.chart.xAxis || obj.chart.yAxis || obj.chart.title)) return obj.chart
    if (obj?.chart?.option) return obj.chart.option
    if (obj?.data && (obj.data.series || obj.data.xAxis || obj.data.yAxis)) return obj.data
  } catch (e) {
    const start = cleaned.indexOf('{')
    const end = cleaned.lastIndexOf('}')
    if (start !== -1 && end > start) {
      let candidate = cleaned.substring(start, end + 1)
      if (candidate.includes('{{')) {
        candidate = candidate.replace(/\{\{/g, '{').replace(/\}\}/g, '}')
      }
      try {
        const obj2 = JSON.parse(candidate)
        if (obj2?.chart && (obj2.chart.series || obj2.chart.xAxis || obj2.chart.yAxis || obj2.chart.title)) return obj2.chart
        if (obj2?.chart?.option) return obj2.chart.option
        if (obj2?.data && (obj2.data.series || obj2.data.xAxis || obj2.data.yAxis)) return obj2.data
        if (obj2 && (obj2.series || obj2.xAxis || obj2.yAxis)) return obj2
      } catch (e2) {}
    }
  }
  return null
}

function tryParseAnalysisContent(text) {
  if (!text) return ''
  let cleaned = text.trim()
  if (cleaned.includes('{{')) {
    const fixed = cleaned.replace(/\{\{/g, '{').replace(/\}\}/g, '}')
    try { JSON.parse(fixed); cleaned = fixed } catch(e) {}
  }
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```\w*\n?/, '')
    if (cleaned.endsWith('```')) cleaned = cleaned.slice(0, -3).trim()
  }
  let content = ''
  try {
    const obj = JSON.parse(cleaned)
    const isAnalysis = obj.summary || obj.analysis || (obj.conclusion && Array.isArray(obj.conclusion))
    if (!isAnalysis) return ''
    if (obj.summary) content += `**✨ 结论：** ${obj.summary}\n\n`
    if (obj.analysis) content += `${obj.analysis}\n\n`
    if (obj.conclusion && Array.isArray(obj.conclusion)) {
      content += '**🎯 关键发现：**\n'
      obj.conclusion.forEach(c => { content += `- ${c}\n` })
    }
  } catch(e) {
    const start = cleaned.indexOf('{')
    const end = cleaned.lastIndexOf('}')
    if (start !== -1 && end > start) {
      let candidate = cleaned.substring(start, end + 1)
      if (candidate.includes('{{')) {
        candidate = candidate.replace(/\{\{/g, '{').replace(/\}\}/g, '}')
      }
      try {
        const obj = JSON.parse(candidate)
        const isAnalysis = obj.summary || obj.analysis || (obj.conclusion && Array.isArray(obj.conclusion))
        if (!isAnalysis) return ''
        if (obj.summary) content += `**✨ 结论：** ${obj.summary}\n\n`
        if (obj.analysis) content += `${obj.analysis}\n\n`
        if (obj.conclusion && Array.isArray(obj.conclusion)) {
          content += '**🎯 关键发现：**\n'
          obj.conclusion.forEach(c => { content += `- ${c}\n` })
        }
      } catch(e2) {}
    }
  }
  return content
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

function formatSessionTime(ts) {
  if (!ts) return '会话'
  const d = new Date(ts)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

// 打字动画
function startTypingAnimation() {
  let idx = 0
  typingText.value = typingPhrases[0]
  typingTimer = setInterval(() => {
    idx = (idx + 1) % typingPhrases.length
    typingText.value = typingPhrases[idx]
  }, 2000)
}

function stopTypingAnimation() {
  if (typingTimer) { clearInterval(typingTimer); typingTimer = null }
}

async function loadSessions() {
  try {
    const res = await fetch(`/api/sessions?email=${userInfo?.email || ''}`)
    const data = await res.json()
    if (data.code === 200) sessions.value = data.data || []
  } catch (e) {}
}

async function loadSession(sessionId) {
  try {
    const res = await fetch(`/api/chat_history?email=${userInfo?.email}&session_id=${sessionId}`)
    const data = await res.json()
    if (data.code === 200 && data.data) {
      currentSessionId.value = sessionId
      messages.value = data.data.map(msg => {
        const id = makeMsgId()
        let chartOption = msg.chart_option || null
        if (typeof chartOption === 'string') {
          try { chartOption = JSON.parse(chartOption) } catch(e) { chartOption = null }
        }
        let content = msg.content || ''
        if (msg.role === 'ai' && content.trim().startsWith('{')) {
          const parsedChart = tryParseChartOption(content)
          const parsedAnalysis = tryParseAnalysisContent(content)
          if (parsedChart) chartOption = parsedChart
          if (parsedAnalysis) content = parsedAnalysis
        }
        return { role: msg.role === 'user' ? 'user' : 'ai', content, chartOption, _id: id }
      })
      scrollToBottom()
      nextTick(() => {
        messages.value.forEach(msg => {
          if (msg.chartOption && msg._id) renderChart(msg._id, msg.chartOption)
        })
      })
    }
  } catch (e) {}
}

function newChat() {
  if (currentController) { currentController.abort(); currentController = null }
  messages.value = []
  currentSessionId.value = null
  isTyping.value = false
  stopTypingAnimation()
}

function quickAsk(text) {
  inputText.value = text
  sendMessage()
}

// ===== 统一SSE发送，不再区分chart/analyze =====
function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  let questionText = text
  if (uploadedFile.value) {
    questionText = text + ` [已上传文件: ${uploadedFile.value}]`
    uploadedFile.value = null
  }

  messages.value.push({ role: 'user', content: questionText, _id: makeMsgId() })
  inputText.value = ''
  scrollToBottom()
  isTyping.value = true
  startTypingAnimation()

  const formData = new FormData()
  formData.append('question', questionText)
  formData.append('user_id', userInfo?.email || 'anonymous')
  if (currentSessionId.value) formData.append('session_id', currentSessionId.value)

  const aiMsgId = makeMsgId()
  messages.value.push({ role: 'ai', content: '', _id: aiMsgId, streaming: true })

  currentController = fetchSSE(
    '/api/chat',
    { method: 'POST', isFormData: true, body: formData },
    (data) => {
      const aiMsg = messages.value.find(m => m._id === aiMsgId)
      if (data.content && aiMsg) {
        aiMsg.content += data.content
        scrollToBottom()
      }
      if (data.done) {
        isTyping.value = false
        stopTypingAnimation()
        currentController = null
        if (data.session_id) currentSessionId.value = data.session_id

        if (aiMsg) {
          // 流结束后尝试解析完整内容
          const fullText = aiMsg.content
          const chartOption = tryParseChartOption(fullText)
          const analysisContent = tryParseAnalysisContent(fullText)

          if (chartOption && analysisContent) {
            aiMsg.content = analysisContent
            aiMsg.chartOption = chartOption
          } else if (chartOption) {
            aiMsg.content = ''
            aiMsg.chartOption = chartOption
          } else if (analysisContent) {
            aiMsg.content = analysisContent
          }
          // 否则保留原始markdown文本

          aiMsg.streaming = false
        }

        loadSessions()
        scrollToBottom()
        if (aiMsg?.chartOption) {
          nextTick(() => { renderChart(aiMsgId, aiMsg.chartOption); rerenderAllCharts() })
        }
      }
    },
    (error) => {
      isTyping.value = false
      stopTypingAnimation()
      const aiMsg = messages.value.find(m => m._id === aiMsgId)
      if (aiMsg) aiMsg.content = '呜...出了点小问题，再试一次吧 🥺'
      currentController = null
    }
  )
}

function triggerUpload() {
  if (fileInputRef.value) fileInputRef.value.click()
}

async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const validTypes = ['.csv', '.xlsx', '.xls']
  const fileExt = '.' + file.name.split('.').pop().toLowerCase()
  if (!validTypes.includes(fileExt)) { alert('请上传 CSV 或 Excel 文件哦～ 📄'); return }

  isUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch('/api/upload', { method: 'POST', body: formData })
    const result = await response.json()
    if (result.code === 200) {
      uploadedFile.value = file.name
      const importInfo = result.import_result
      if (importInfo?.success) {
        messages.value.push({
          role: 'ai',
          content: `🎉 太棒了！文件 **${result.filename}** 已上传成功，导入了 ${importInfo.rows} 条数据～现在可以问我关于这些数据的问题啦！`,
          _id: makeMsgId()
        })
      } else {
        messages.value.push({
          role: 'ai',
          content: `📎 文件 **${result.filename}** 已上传，但数据导入遇到了些问题：${importInfo?.error || '未知错误'} 😅`,
          _id: makeMsgId()
        })
      }
      scrollToBottom()
    } else {
      alert('上传失败：' + (result.msg || '未知错误'))
    }
  } catch (error) {
    alert('上传失败，请重试！')
  } finally {
    isUploading.value = false
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

async function saveSettings() {
  try {
    const params = new URLSearchParams()
    params.append('email', userInfo?.email || '')
    if (settings.value.detail_level) params.append('detail_level', settings.value.detail_level)
    if (settings.value.default_chart_type) params.append('default_chart_type', settings.value.default_chart_type)
    if (settings.value.theme) params.append('theme', settings.value.theme)
    await fetch(`/api/update_preferences?${params.toString()}`, {method: 'POST'})
    if (userInfo) {
      userInfo.preferences = {...settings.value}
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
    }
    showSettings.value = false
  } catch (e) {
  }
}

function handleLogout() {
  localStorage.removeItem('userInfo')
  router.push('/')
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #f8f9ff;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 60px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: relative;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b9d, #c44dff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
  color: #fff;
  box-shadow: 0 4px 12px rgba(196, 77, 255, 0.3);
}

.user-name {
  font-size: 15px;
  font-weight: 600;
}

.user-dept {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.sidebar-toggle {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.3);
  font-size: 16px;
  cursor: pointer;
}

.sidebar-toggle:hover {
  color: #fff;
}

.new-chat-btn {
  margin: 16px 12px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(196, 77, 255, 0.2));
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  transition: all 0.3s;
}

.new-chat-btn:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.35), rgba(196, 77, 255, 0.35));
  border-color: rgba(255, 255, 255, 0.4);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.session-title {
  padding: 12px 16px 8px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  margin: 2px 8px;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.session-item.active {
  background: rgba(102, 126, 234, 0.25);
  color: #fff;
}

.session-empty {
  padding: 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.25);
  text-align: center;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.settings-btn, .logout-btn {
  padding: 10px 12px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
  text-align: left;
  transition: all 0.2s;
}

.settings-btn:hover, .logout-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

/* ===== 主区域 ===== */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.08);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bot-mascot {
  font-size: 32px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0)
  }
  50% {
    transform: translateY(-6px)
  }
}

.title {
  font-size: 18px;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.bot-status {
  font-size: 12px;
  color: #91CC75;
}

.user-greeting {
  font-size: 14px;
  color: #666;
  background: #f8f9ff;
  padding: 8px 16px;
  border-radius: 20px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scroll-behavior: smooth;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.mascot-bounce {
  font-size: 80px;
  margin-bottom: 20px;
  animation: bounce 2s ease infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0)
  }
  40% {
    transform: translateY(-20px)
  }
  60% {
    transform: translateY(-10px)
  }
}

.welcome-title {
  font-size: 26px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.welcome-sub {
  font-size: 15px;
  color: #888;
  margin-bottom: 28px;
  max-width: 400px;
  line-height: 1.6;
}

.suggestions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.suggestion {
  padding: 12px 20px;
  font-size: 14px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.12);
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.suggestion:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
  background: #f0f0ff;
}

/* 消息 */
.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  align-items: flex-start;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px)
  }
  to {
    opacity: 1;
    transform: translateY(0)
  }
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 16px;
  background: linear-gradient(135deg, #ff6b9d, #c44dff);
  color: #fff;
}

.message-avatar.ai-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  font-size: 20px;
}

.message-content {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.7;
  font-size: 15px;
}

.message-content.user {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-content.ai {
  background: #fff;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.chart-container {
  width: 100%;
  min-height: 400px;
  height: 450px;
  background: #fff;
  border-radius: 12px;
  margin-top: 12px;
}

/* 打字动画 */
.typing {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
}

.typing-text {
  font-size: 14px;
  color: #999;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: #667eea;
  border-radius: 50%;
  animation: pulse 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {
  0%, 60%, 100% {
    transform: scale(1);
    opacity: 0.4
  }
  30% {
    transform: scale(1.3);
    opacity: 1
  }
}

/* 输入区 */
.input-area {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 -2px 12px rgba(102, 126, 234, 0.06);
  flex-shrink: 0;
  align-items: center;
}

.upload-btn {
  width: 42px;
  height: 42px;
  font-size: 20px;
  background: #f0f0ff;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s;
}

.upload-btn:hover:not(:disabled) {
  background: #667eea;
  color: #fff;
  transform: scale(1.05);
}

.upload-btn:disabled {
  background: #eee;
  cursor: not-allowed;
}

.input-area .input {
  flex: 1;
  padding: 14px 20px;
  font-size: 15px;
  border: 2px solid #e8e8ff;
  border-radius: 28px;
  outline: none;
  transition: all 0.3s;
  background: #fafaff;
}

.input-area .input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
}

.send-btn {
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 28px;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35);
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s;
}

.modal-content {
  width: 460px;
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #f0f0ff;
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: #f5f5f5;
}

.modal-body {
  padding: 24px;
}

.setting-item {
  margin-bottom: 24px;
}

.setting-item label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.setting-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.setting-option {
  padding: 10px 20px;
  border: 2px solid #e8e8ff;
  border-radius: 12px;
  background: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.setting-option.active {
  border-color: #667eea;
  background: #f0f0ff;
  color: #667eea;
  font-weight: 600;
}

.setting-option:hover:not(.active) {
  border-color: #c4c4ff;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #f0f0ff;
  text-align: right;
}

.save-btn {
  padding: 12px 36px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}
</style>

<!-- Markdown全局样式 - v-html渲染需要非scoped样式 -->
<style>
.markdown-body {
  color: #333;
  line-height: 1.7;
  font-size: 14px;
}

.markdown-body h1 {
  font-size: 20px;
  font-weight: 700;
  color: #4a5568;
  margin: 16px 0 10px;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 6px;
}

.markdown-body h2 {
  font-size: 17px;
  font-weight: 700;
  color: #5a67d8;
  margin: 14px 0 8px;
}

.markdown-body h3 {
  font-size: 15px;
  font-weight: 600;
  color: #667eea;
  margin: 12px 0 6px;
}

.markdown-body h4 {
  font-size: 14px;
  font-weight: 600;
  color: #718096;
  margin: 10px 0 5px;
}

.markdown-body p {
  margin-bottom: 10px;
}

.markdown-body ul, .markdown-body ol {
  padding-left: 22px;
  margin-bottom: 10px;
}

.markdown-body li {
  margin-bottom: 4px;
}

.markdown-body code {
  background: #f0f0ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #667eea;
}

.markdown-body pre {
  background: #f5f5ff;
  padding: 12px;
  border-radius: 10px;
  overflow-x: auto;
}

.markdown-body strong {
  color: #667eea;
  font-weight: 600;
}

.markdown-body blockquote {
  border-left: 4px solid #667eea;
  padding: 8px 14px;
  margin: 10px 0;
  background: #f7f7ff;
  border-radius: 0 8px 8px 0;
  color: #555;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 14px 0;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  font-size: 13px;
}

.markdown-body thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.markdown-body th {
  padding: 10px 14px;
  text-align: left;
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
}

.markdown-body td {
  padding: 9px 14px;
  border-bottom: 1px solid #edf2f7;
  color: #4a5568;
}

.markdown-body tbody tr:nth-child(even) {
  background: #f7fafc;
}

.markdown-body tbody tr:hover {
  background: #edf2f7;
}

.markdown-body tbody tr:last-child td {
  border-bottom: none;
}
</style>
