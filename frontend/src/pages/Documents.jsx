import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDocuments = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No authentication token found. Please get a token first.');
        return;
      }

      const response = await axios.get('http://localhost:8000/documents', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setDocuments(response.data.documents || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError(err.response?.data?.detail || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Document Library</h1>
        <p className="page-subtitle">Browse and manage your knowledge base documents</p>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="card-title">📚 Documents</h3>
              <p className="card-subtitle">
                {documents.length} document{documents.length !== 1 ? 's' : ''} in your knowledge base
              </p>
            </div>
            <button 
              onClick={fetchDocuments}
              className="btn btn-secondary"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading"></span>
                  Loading...
                </>
              ) : (
                'Refresh'
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {loading && documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="loading" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📄</div>
            <h4>No Documents Found</h4>
            <p className="text-secondary">
              Upload some documents to get started with your knowledge base.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc, index) => (
              <div key={doc.id || index} className="document-item">
                <div className="document-info">
                  <div className="document-name">{doc.filename || doc.name || 'Unknown Document'}</div>
                  <div className="document-meta">
                    <span>ID: {doc.id || doc.document_id || 'N/A'}</span>
                    {doc.upload_date && (
                      <span> • Uploaded: {formatDate(doc.upload_date)}</span>
                    )}
                    {doc.file_size && (
                      <span> • Size: {formatFileSize(doc.file_size)}</span>
                    )}
                    {doc.chunks_count && (
                      <span> • Chunks: {doc.chunks_count}</span>
                    )}
                    {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                      <span> • Has metadata</span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                    <button 
                      className="btn btn-sm btn-outline"
                      onClick={() => alert(JSON.stringify(doc.metadata, null, 2))}
                    >
                      View Metadata
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-2 mt-5">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📊 Document Statistics</h3>
            <p className="card-subtitle">Overview of your knowledge base</p>
          </div>

          <div className="grid grid-2">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{documents.length}</div>
              <div className="text-sm text-blue-600">Total Documents</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {documents.reduce((sum, doc) => sum + (doc.chunks_count || 0), 0)}
              </div>
              <div className="text-sm text-green-600">Total Chunks</div>
            </div>
          </div>

          <div className="mt-4">
            <h4>File Types:</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {Array.from(new Set(documents.map(doc => {
                const filename = doc.filename || doc.name || '';
                return filename.split('.').pop()?.toUpperCase() || 'UNKNOWN';
              }))).map(type => (
                <span key={type} className="px-2 py-1 bg-gray-100 rounded text-sm">
                  {type}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🔍 Search & Filter</h3>
            <p className="card-subtitle">Find specific documents</p>
          </div>

          <div>
            <p className="text-secondary mb-4">
              Use the search functionality in the Ask or Chat pages to find information within your documents.
            </p>

            <h4>Search Tips:</h4>
            <ul>
              <li>Ask specific questions about document content</li>
              <li>Reference document names or topics</li>
              <li>Use natural language queries</li>
              <li>Combine multiple concepts in one question</li>
            </ul>

            <div className="mt-4">
              <h4>Recent Activity:</h4>
              <p className="text-sm text-secondary">
                Documents are automatically indexed when uploaded and can be searched immediately.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoint</h3>
          <p className="card-subtitle">Documents endpoint details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>GET /documents</h4>
            <p>Retrieve all documents in the knowledge base</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              curl -H "Authorization: Bearer YOUR_TOKEN" \
                http://localhost:8000/documents
            </pre>
          </div>
          
          <div>
            <h4>Response Format</h4>
            <p>Returns list of documents with metadata</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "documents": [
    {
      "id": "doc_123",
      "filename": "document.pdf",
      "upload_date": "2024-01-01T00:00:00Z",
      "chunks_count": 15,
      "metadata": {...}
    }
  ]
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Documents;


