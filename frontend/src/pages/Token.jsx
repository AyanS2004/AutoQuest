import React, { useState } from 'react';
import axios from 'axios';

function Token() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post('http://localhost:8000/auth/token', {
        username,
        password
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      setMessage('Token obtained successfully! You can now use other features.');
      setMessageType('success');
      setUsername('');
      setPassword('');
    } catch (error) {
      console.error('Error getting token:', error);
      setMessage(error.response?.data?.detail || 'Failed to get token');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const clearToken = () => {
    localStorage.removeItem('token');
    setMessage('Token cleared successfully!');
    setMessageType('success');
  };

  const currentToken = localStorage.getItem('token');

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Authentication</h1>
        <p className="page-subtitle">Get your JWT token to access the AutoQuest API</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🔐 Get Token</h3>
            <p className="card-subtitle">Request a new authentication token</p>
          </div>

          {message && (
            <div className={`alert alert-${messageType}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="username" className="form-label">Username</label>
              <input
                type="text"
                id="username"
                className="form-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading"></span>
                  Getting Token...
                </>
              ) : (
                'Get Token'
              )}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🔑 Current Token</h3>
            <p className="card-subtitle">Manage your authentication token</p>
          </div>

          {currentToken ? (
            <div>
              <div className="alert alert-success">
                ✅ Token is stored and ready to use
              </div>
              
              <div className="form-group">
                <label className="form-label">Token Preview</label>
                <input
                  type="text"
                  className="form-input"
                  value={`${currentToken.substring(0, 20)}...`}
                  readOnly
                />
              </div>

              <button 
                onClick={clearToken}
                className="btn btn-danger"
              >
                Clear Token
              </button>
            </div>
          ) : (
            <div className="alert alert-warning">
              ⚠️ No token stored. Get a token to access API features.
            </div>
          )}

          <div className="mt-4">
            <h4>How it works:</h4>
            <ol>
              <li>Enter your username and password</li>
              <li>Click "Get Token" to request authentication</li>
              <li>The token will be stored locally in your browser</li>
              <li>All API requests will automatically include this token</li>
            </ol>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoints</h3>
          <p className="card-subtitle">Available authentication endpoints</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>POST /auth/token</h4>
            <p>Get a JWT token using username and password</p>
            <code className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "username": "your_username",
  "password": "your_password"
}`}
            </code>
          </div>
          
          <div>
            <h4>Response</h4>
            <p>Returns an access token for API authentication</p>
            <code className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}`}
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Token;


