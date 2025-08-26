import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Health() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const checkHealth = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const config = token ? { headers: { Authorization: `Bearer ${token}` } } : {};
      
      const response = await axios.get('http://localhost:8000/health', config);
      setHealth(response.data);
    } catch (err) {
      console.error('Error checking health:', err);
      setError(err.response?.data?.detail || 'Failed to check health status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'ok':
        return '✅';
      case 'unhealthy':
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      default:
        return '❓';
    }
  };

  const getStatusClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'ok':
        return 'alert-success';
      case 'unhealthy':
      case 'error':
        return 'alert-error';
      case 'warning':
        return 'alert-warning';
      default:
        return 'alert-info';
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">System Health</h1>
        <p className="page-subtitle">Monitor the status of all AutoQuest services</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📊 Health Status</h3>
          <p className="card-subtitle">Current system status and service health</p>
        </div>

        <div className="flex justify-between items-center mb-4">
          <button 
            onClick={checkHealth}
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading"></span>
                Checking...
              </>
            ) : (
              'Refresh Health'
            )}
          </button>

          {health && (
            <div className="text-sm text-secondary">
              Last checked: {new Date().toLocaleTimeString()}
            </div>
          )}
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {health && (
          <div className="grid grid-2">
            <div>
              <h4>Overall Status</h4>
              <div className={`alert ${getStatusClass(health.status)}`}>
                {getStatusIcon(health.status)} {health.status}
              </div>
              
              {health.version && (
                <div className="mt-3">
                  <strong>Version:</strong> {health.version}
                </div>
              )}
              
              {health.timestamp && (
                <div className="mt-1">
                  <strong>Timestamp:</strong> {new Date(health.timestamp).toLocaleString()}
                </div>
              )}
            </div>

            <div>
              <h4>Services</h4>
              {health.services && Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex justify-between items-center p-2 mb-2 bg-gray-50 rounded">
                  <span className="font-medium">{service}</span>
                  <span className={`px-2 py-1 rounded text-sm ${getStatusClass(status)}`}>
                    {getStatusIcon(status)} {status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {health && health.details && (
          <div className="mt-4">
            <h4>Detailed Information</h4>
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
              {JSON.stringify(health.details, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="grid grid-2 mt-5">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🔍 What's Monitored</h3>
            <p className="card-subtitle">Services and components checked</p>
          </div>
          
          <ul>
            <li>FastAPI application status</li>
            <li>Vector database connectivity</li>
            <li>RAG engine availability</li>
            <li>External API dependencies</li>
            <li>System resources</li>
            <li>Configuration validation</li>
          </ul>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🚨 Troubleshooting</h3>
            <p className="card-subtitle">Common issues and solutions</p>
          </div>
          
          <div>
            <h4>If services are unhealthy:</h4>
            <ol>
              <li>Check if the backend server is running</li>
              <li>Verify database connections</li>
              <li>Check environment variables</li>
              <li>Review application logs</li>
              <li>Restart the application if needed</li>
            </ol>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoint</h3>
          <p className="card-subtitle">Health check endpoint details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>GET /health</h4>
            <p>Returns comprehensive health status of all services</p>
            <code className="block p-2 bg-gray-100 rounded text-sm">
              curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/health
            </code>
          </div>
          
          <div>
            <h4>Response Format</h4>
            <p>JSON object with status, services, and details</p>
            <code className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "services": {
    "database": "healthy",
    "vector_store": "healthy"
  }
}`}
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Health;


