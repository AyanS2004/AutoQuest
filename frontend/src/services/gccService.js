/**
 * GCC Service - Handles API calls to GCC extraction endpoints
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

class GCCService {
  constructor() {
    this.baseUrl = API_BASE;
  }

  async getAuthToken() {
    // Get token from localStorage or prompt user
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error('No authentication token found. Please get a token first.');
    }
    return token;
  }

  async makeRequest(endpoint, options = {}) {
    const token = await this.getAuthToken();
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      },
      ...options
    };

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async startExtraction(config) {
    return this.makeRequest('/gcc/start', {
      method: 'POST',
      body: JSON.stringify({
        input_file: config.inputFile,
        output_file: config.outputFile,
        template_file: config.templateFile,
        debug_port: config.debugPort
      })
    });
  }

  async getStatus(sessionId) {
    return this.makeRequest(`/gcc/status/${sessionId}`);
  }

  async stopExtraction(sessionId) {
    return this.makeRequest(`/gcc/stop/${sessionId}`, {
      method: 'POST'
    });
  }

  async downloadResults(filename) {
    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/gcc/download/${filename}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Poll status updates
  async pollStatus(sessionId, onUpdate, onError, interval = 2000) {
    const poll = async () => {
      try {
        const status = await this.getStatus(sessionId);
        onUpdate(status);
        
        // Continue polling if still running
        if (['starting', 'running'].includes(status.status)) {
          setTimeout(poll, interval);
        }
      } catch (error) {
        onError(error);
      }
    };

    poll();
  }
}

export default new GCCService();
