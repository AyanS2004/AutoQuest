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
      const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
      if (!token) {
        setError('No authentication token found. Please get a token first.');
        return;
      }

      const response = await axios.get('http://localhost:8000/documents', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setDocuments(response.data.documents || response.data || []);
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


      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="card-title">Documents</h3>
              <p className="card-subtitle">
                {documents.length} document{documents.length !== 1 ? 's' : ''} in your knowledge base
              </p>
            </div>
            <button 
              onClick={fetchDocuments}
              className="btn btn-secondary btn-sm"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="animate-spin inline-block h-4 w-4 border-2 border-input border-t-transparent rounded-full mr-2" />
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
            <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent mx-auto mb-4"></div>
            <p>Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📄</div>
            <h4 className="text-lg font-semibold">No Documents Found</h4>
            <p className="text-muted-foreground">
              Upload some documents to get started with your knowledge base.
            </p>
          </div>
        ) : (
          <div className="space-y-3 p-6 pt-0">
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
                    {(doc.chunks_count || doc.chunk_count) && (
                      <span> • Chunks: {doc.chunks_count || doc.chunk_count}</span>
                    )}
                    {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                      <span> • Has metadata</span>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2">
                  {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                    <button 
                      className="btn btn-outline btn-sm"
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-5">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Document Statistics</h3>
            <p className="card-subtitle">Overview of your knowledge base</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-6 pt-0">
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold">{documents.length}</div>
              <div className="text-sm text-muted-foreground">Total Documents</div>
            </div>
            
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold">
                {documents.reduce((sum, doc) => sum + (doc.chunks_count || doc.chunk_count || 0), 0)}
              </div>
              <div className="text-sm text-muted-foreground">Total Chunks</div>
            </div>
          </div>

          <div className="p-6 pt-0">
            <h4 className="font-medium">File Types:</h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {Array.from(new Set(documents.map(doc => {
                const filename = doc.filename || doc.name || '';
                return filename.split('.').pop()?.toUpperCase() || 'UNKNOWN';
              }))).map(type => (
                <span key={type} className="px-2 py-1 bg-muted rounded text-xs">
                  {type}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Search & Filter</h3>
            <p className="card-subtitle">Find specific documents</p>
          </div>

          <div className="p-6 pt-0">
            <p className="text-muted-foreground mb-4">
              Use the search functionality in the Ask or Chat pages to find information within your documents.
            </p>

            <h4 className="font-medium">Search Tips:</h4>
            <ul className="list-disc pl-5 space-y-1 text-sm">
              <li>Ask specific questions about document content</li>
              <li>Reference document names or topics</li>
              <li>Use natural language queries</li>
              <li>Combine multiple concepts in one question</li>
            </ul>

            <div className="mt-4">
              <h4 className="font-medium">Recent Activity:</h4>
              <p className="text-sm text-muted-foreground">
                Documents are automatically indexed when uploaded and can be searched immediately.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">API Endpoint</h3>
          <p className="card-subtitle">Documents endpoint details</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 pt-0">
          <div>
            <h4 className="font-medium">GET /documents</h4>
            <p className="text-sm text-muted-foreground">Retrieve all documents in the knowledge base</p>
            <pre className="block p-2 bg-muted rounded text-sm mt-2">
              curl -H "Authorization: Bearer YOUR_TOKEN" \
                http://localhost:8000/documents
            </pre>
          </div>
          
          <div>
            <h4 className="font-medium">Response Format</h4>
            <p className="text-sm text-muted-foreground">Returns list of documents with metadata</p>
            <pre className="block p-2 bg-muted rounded text-sm mt-2">
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


