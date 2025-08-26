import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError('');

    // Add user message to chat
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found. Please get a token first.');
        return;
      }

      const response = await axios.post('http://localhost:8000/chat', {
        message: userMessage,
        history: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      // Add assistant response to chat
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources || [],
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error in chat:', err);
      setError(err.response?.data?.detail || 'Failed to get response');
      
      // Add error message to chat
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError('');
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Interactive Chat</h1>
        <p className="page-subtitle">Have a conversation with your knowledge base</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="card-title">💬 Chat Interface</h3>
                <p className="card-subtitle">
                  {messages.length} message{messages.length !== 1 ? 's' : ''} in conversation
                </p>
              </div>
              <button 
                onClick={clearChat}
                className="btn btn-outline btn-sm"
                disabled={loading}
              >
                Clear Chat
              </button>
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="chat-container">
            <div className="chat-messages">
              {messages.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">💬</div>
                  <h4>Start a Conversation</h4>
                  <p className="text-secondary">
                    Ask questions about your documents and get intelligent responses.
                  </p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={index} className={`chat-message ${message.role}`}>
                    <div className="flex justify-between items-start mb-2">
                      <strong className="text-sm">
                        {message.role === 'user' ? 'You' : 'AutoQuest'}
                      </strong>
                      <span className="text-xs text-secondary">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    
                    <div className="message-content">
                      {message.content}
                    </div>

                    {message.sources && message.sources.length > 0 && (
                      <div className="sources mt-3">
                        <h5 className="sources-title text-sm">📚 Sources:</h5>
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="source-item text-xs">
                            <strong>Document:</strong> {source.document_name || 'Unknown'}
                            {source.page && <span> | <strong>Page:</strong> {source.page}</span>}
                            {source.chunk && (
                              <div className="mt-1">
                                <strong>Relevant:</strong> "{source.chunk.substring(0, 150)}..."
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {message.error && (
                      <div className="text-red-500 text-sm mt-2">
                        ⚠️ This response encountered an error
                      </div>
                    )}
                  </div>
                ))
              )}

              {loading && (
                <div className="chat-message assistant">
                  <div className="flex items-center gap-2">
                    <span className="loading"></span>
                    <span>Thinking...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="chat-input">
              <input
                type="text"
                className="form-input"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={loading}
              />
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !inputMessage.trim()}
              >
                Send
              </button>
            </form>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💡 Chat Features</h3>
            <p className="card-subtitle">Conversational AI with context</p>
          </div>

          <div>
            <h4>How it works:</h4>
            <ol>
              <li><strong>Context Awareness:</strong> Remembers conversation history</li>
              <li><strong>Document Retrieval:</strong> Finds relevant information</li>
              <li><strong>Intelligent Responses:</strong> Generates contextual answers</li>
              <li><strong>Source Citations:</strong> Shows where information comes from</li>
            </ol>

            <h4 className="mt-4">Best Practices:</h4>
            <ul>
              <li>Ask follow-up questions naturally</li>
              <li>Reference previous parts of the conversation</li>
              <li>Be specific about what you want to know</li>
              <li>Use the conversation to explore topics deeply</li>
            </ul>

            <h4 className="mt-4">Example Conversation:</h4>
            <div className="bg-gray-50 p-3 rounded text-sm">
              <p><strong>You:</strong> "What is the main topic of the document?"</p>
              <p><strong>AutoQuest:</strong> "The document discusses..."</p>
              <p><strong>You:</strong> "Can you elaborate on that?"</p>
              <p><strong>AutoQuest:</strong> "Based on the context..."</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoint</h3>
          <p className="card-subtitle">Chat endpoint details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>POST /chat</h4>
            <p>Send a message and get a contextual response</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{{"message": "Hello", "history": []}}' \
                http://localhost:8000/chat
            </pre>
          </div>
          
          <div>
            <h4>Response Format</h4>
            <p>Returns response with conversation context</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "response": "Hello! How can I help you?",
  "sources": [...],
  "conversation_id": "conv_123"
}`}
            </pre>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">🎯 Conversation Tips</h3>
          <p className="card-subtitle">Make the most of your chat experience</p>
        </div>
        
        <div className="grid grid-3">
          <div>
            <h4>Getting Started:</h4>
            <ul>
              <li>"What documents do you have?"</li>
              <li>"Summarize the main topics"</li>
              <li>"What are the key findings?"</li>
            </ul>
          </div>
          
          <div>
            <h4>Deep Dives:</h4>
            <ul>
              <li>"Tell me more about X"</li>
              <li>"How does this relate to Y?"</li>
              <li>"What are the implications?"</li>
            </ul>
          </div>
          
          <div>
            <h4>Analysis:</h4>
            <ul>
              <li>"Compare and contrast A and B"</li>
              <li>"What are the pros and cons?"</li>
              <li>"How does this apply to Z?"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;


