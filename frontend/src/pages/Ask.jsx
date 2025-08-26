import React, { useState } from 'react';
import axios from 'axios';

function Ask() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer('');
    setSources([]);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found. Please get a token first.');
        return;
      }

      const response = await axios.post('http://localhost:8000/ask', {
        question: question.trim()
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setAnswer(response.data.answer);
      setSources(response.data.sources || []);
    } catch (err) {
      console.error('Error asking question:', err);
      setError(err.response?.data?.detail || 'Failed to get answer');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    setQuestion('');
    setAnswer('');
    setSources([]);
    setError('');
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Ask Questions</h1>
        <p className="page-subtitle">Query your knowledge base with intelligent RAG-powered answers</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">❓ Ask a Question</h3>
            <p className="card-subtitle">Get intelligent answers from your documents</p>
          </div>

          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="question" className="form-label">Your Question</label>
              <textarea
                id="question"
                className="form-textarea"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask anything about your uploaded documents..."
                rows={4}
                required
              />
            </div>

            <div className="flex gap-3">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !question.trim()}
              >
                {loading ? (
                  <>
                    <span className="loading"></span>
                    Thinking...
                  </>
                ) : (
                  'Ask Question'
                )}
              </button>

              <button 
                type="button" 
                className="btn btn-outline"
                onClick={clearForm}
                disabled={loading}
              >
                Clear
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💡 How It Works</h3>
            <p className="card-subtitle">RAG-powered question answering</p>
          </div>

          <div>
            <h4>Process:</h4>
            <ol>
              <li><strong>Question Analysis:</strong> Understand your question</li>
              <li><strong>Document Retrieval:</strong> Find relevant document chunks</li>
              <li><strong>Context Building:</strong> Gather supporting information</li>
              <li><strong>Answer Generation:</strong> Create comprehensive response</li>
              <li><strong>Source Citation:</strong> Provide reference sources</li>
            </ol>

            <h4 className="mt-4">Best Practices:</h4>
            <ul>
              <li>Ask specific, focused questions</li>
              <li>Use natural language</li>
              <li>Reference specific documents or topics</li>
              <li>Ask follow-up questions for clarification</li>
            </ul>
          </div>
        </div>
      </div>

      {answer && (
        <div className="card mt-5">
          <div className="card-header">
            <h3 className="card-title">🤖 Answer</h3>
            <p className="card-subtitle">AI-generated response based on your documents</p>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-lg leading-relaxed">{answer}</p>
          </div>

          {sources && sources.length > 0 && (
            <div className="sources mt-4">
              <h4 className="sources-title">📚 Sources</h4>
              {sources.map((source, index) => (
                <div key={index} className="source-item">
                  <strong>Document:</strong> {source.document_name || 'Unknown'}
                  {source.page && <span> | <strong>Page:</strong> {source.page}</span>}
                  {source.chunk && (
                    <div className="mt-2 text-sm">
                      <strong>Relevant Text:</strong> "{source.chunk.substring(0, 200)}..."
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoint</h3>
          <p className="card-subtitle">Ask endpoint details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>POST /ask</h4>
            <p>Ask a question and get an answer with sources</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{{"question": "What is the main topic?"}}' \
                http://localhost:8000/ask
            </pre>
          </div>
          
          <div>
            <h4>Response Format</h4>
            <p>Returns answer with source citations</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "answer": "The main topic is...",
  "sources": [
    {
      "document_name": "document.pdf",
      "page": 1,
      "chunk": "relevant text..."
    }
  ]
}`}
            </pre>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">🎯 Example Questions</h3>
          <p className="card-subtitle">Try these types of questions</p>
        </div>
        
        <div className="grid grid-3">
          <div>
            <h4>General Questions:</h4>
            <ul>
              <li>"What is the main topic of the document?"</li>
              <li>"Summarize the key points"</li>
              <li>"What are the main conclusions?"</li>
            </ul>
          </div>
          
          <div>
            <h4>Specific Questions:</h4>
            <ul>
              <li>"What does the document say about X?"</li>
              <li>"How does the process work?"</li>
              <li>"What are the requirements for Y?"</li>
            </ul>
          </div>
          
          <div>
            <h4>Comparative Questions:</h4>
            <ul>
              <li>"What are the differences between A and B?"</li>
              <li>"How does this compare to that?"</li>
              <li>"What are the pros and cons?"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Ask;


