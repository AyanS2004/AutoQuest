import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token') || localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // leave token as-is; allow UI to handle re-auth
    }
    return Promise.reject(error)
  }
)

// Authentication
export const authAPI = {
  getToken: () => api.get('/token'),
  validateToken: (token) => api.post('/validate-token', { token }),
}

// Health and Status
export const healthAPI = {
  getHealth: () => api.get('/health'),
  getMetrics: () => api.get('/metrics'),
}

// Documents
export const documentsAPI = {
  upload: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    })
  },
  
  list: () => api.get('/documents'),
  
  delete: (documentId) => api.delete(`/documents/${documentId}`),
  
  getInfo: (documentId) => api.get(`/documents/${documentId}`),
}

// Questions and RAG
export const ragAPI = {
  ask: (question, options = {}) => 
    api.post('/ask', { question, ...options }),
  
  batchAsk: (questions) => 
    api.post('/batch-ask', { questions }),
  
  search: (query, filters = {}) => 
    api.post('/search', { query, filters }),
}

// Chat
export const chatAPI = {
  sendMessage: (messages, conversationId = null) => 
    api.post('/chat', { messages, conversation_id: conversationId }),
  
  getConversations: () => api.get('/conversations'),
  
  deleteConversation: (conversationId) => 
    api.delete(`/conversations/${conversationId}`),
}

// GCC Extractor
export const gccAPI = {
  startSession: (config) => 
    api.post('/gcc/start', config),
  
  getSession: (sessionId) => 
    api.get(`/gcc/session/${sessionId}`),
  
  getSessions: () => 
    api.get('/gcc/sessions'),
  
  stopSession: (sessionId) => 
    api.post(`/gcc/session/${sessionId}/stop`),
  
  getProgress: (sessionId) => 
    api.get(`/gcc/session/${sessionId}/progress`),
  
  getResults: (sessionId) => 
    api.get(`/gcc/session/${sessionId}/results`),
  
  exportResults: (sessionId, format = 'excel') => 
    api.get(`/gcc/session/${sessionId}/export`, {
      params: { format },
      responseType: 'blob',
    }),
}

// Data Management (optional backend)
export const dataAPI = {
  getCompanies: (filters = {}) => 
    api.get('/data/companies', { params: filters }),
  
  getCompany: (companyId) => 
    api.get(`/data/companies/${companyId}`),
  
  updateCompany: (companyId, data) => 
    api.put(`/data/companies/${companyId}`, data),
  
  deleteCompany: (companyId) => 
    api.delete(`/data/companies/${companyId}`),
  
  exportData: (format = 'excel', filters = {}) => 
    api.get('/data/export', {
      params: { format, ...filters },
      responseType: 'blob',
    }),
}

// Logs and Monitoring
export const logsAPI = {
  getLogs: (level = 'all', limit = 100) => 
    api.get('/logs', { params: { level, limit } }),
  
  getRealTimeLogs: () => 
    api.get('/logs/stream'),
  
  getErrors: () => api.get('/logs/errors'),
  
  clearLogs: () => api.delete('/logs'),
}

// WebSocket connection for real-time updates
export class WebSocketService {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.listeners = new Map()
  }

  connect() {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws'
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.notifyListeners(data.type, data.payload)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.attemptReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }

  subscribe(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, [])
    }
    this.listeners.get(type).push(callback)

    return () => {
      const callbacks = this.listeners.get(type)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  notifyListeners(type, payload) {
    const callbacks = this.listeners.get(type)
    if (callbacks) {
      callbacks.forEach(callback => callback(payload))
    }
  }

  send(type, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

// Create singleton WebSocket instance
export const wsService = new WebSocketService()

// Error handling utility
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response
    return {
      status,
      message: data?.detail || data?.message || `HTTP ${status} error`,
      data
    }
  } else if (error.request) {
    // Request was made but no response received
    return {
      status: 0,
      message: 'Network error - no response from server',
      data: null
    }
  } else {
    // Something else happened
    return {
      status: 0,
      message: error.message || 'Unknown error occurred',
      data: null
    }
  }
}

export default api
