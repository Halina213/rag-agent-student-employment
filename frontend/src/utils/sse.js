/**
 * SSE (Server-Sent Events) fetch utility
 * @param {string} url - 请求URL
 * @param {Object} options - 请求配置
 * @param {string} options.method - HTTP方法，默认GET
 * @param {Object} options.headers - 请求头
 * @param {Object|string} options.body - 请求体
 * @param {Function} onMessage - 消息回调，接收解析后的数据对象
 * @param {Function} onError - 错误回调
 * @returns {AbortController} 可取消请求的控制器
 */
export function fetchSSE(url, options = {}, onMessage, onError) {
  const controller = new AbortController()
  
  const defaultHeaders = {
    'Content-Type': 'application/json'
  }
  
  const fetchOptions = {
    method: options.method || 'GET',
    headers: {
      ...defaultHeaders,
      ...options.headers
    },
    signal: controller.signal
  }
  
  if (options.body) {
    if (options.method === 'POST') {
      // 支持 form-data 和 json
      if (options.isFormData) {
        fetchOptions.body = options.body
        delete fetchOptions.headers['Content-Type']
      } else {
        fetchOptions.body = typeof options.body === 'string' 
          ? options.body 
          : JSON.stringify(options.body)
      }
    }
  }
  
  fetch(url, fetchOptions)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            // 处理缓冲区中剩余的数据
            if (buffer.trim()) {
              processLine(buffer.trim())
            }
            return
          }
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            processLine(line)
          }
          
          read()
        }).catch(error => {
          if (error.name !== 'AbortError' && onError) {
            onError(error)
          }
        })
      }
      
      function processLine(line) {
        // SSE 格式: data: {...}
        if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          if (data) {
            try {
              const parsed = JSON.parse(data)
              if (onMessage) {
                onMessage(parsed)
              }
            } catch (e) {
              // 如果不是JSON，可能是普通文本
              if (onMessage) {
                onMessage({ content: data, done: false })
              }
            }
          }
        }
      }
      
      read()
    })
    .catch(error => {
      if (error.name !== 'AbortError' && onError) {
        onError(error)
      }
    })
  
  return controller
}
