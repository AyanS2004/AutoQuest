import React, { useState } from 'react';
import axios from 'axios';

function Upload() {
  const [file, setFile] = useState(null);
  const [metadata, setMetadata] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage('Please select a file to upload');
      setMessageType('error');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setMessage('No authentication token found. Please get a token first.');
        setMessageType('error');
        return;
      }

      const formData = new FormData();
      formData.append('file', file);
      
      if (metadata.trim()) {
        try {
          const parsedMetadata = JSON.parse(metadata);
          formData.append('metadata', JSON.stringify(parsedMetadata));
        } catch (e) {
          setMessage('Invalid JSON in metadata field');
          setMessageType('error');
          setLoading(false);
          return;
        }
      }

      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setMessage('File uploaded successfully! Document has been processed and indexed.');
      setMessageType('success');
      setFile(null);
      setMetadata('');
      
      // Reset file input
      const fileInput = document.getElementById('file-input');
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading file:', error);
      setMessage(error.response?.data?.detail || 'Failed to upload file');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    setFile(null);
    setMetadata('');
    setMessage('');
    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Document Upload</h1>
        <p className="page-subtitle">Add documents to your knowledge base for intelligent analysis</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📁 Upload Document</h3>
            <p className="card-subtitle">Upload and process documents for RAG analysis</p>
          </div>

          {message && (
            <div className={`alert alert-${messageType}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="file-input" className="form-label">Select File</label>
              <input
                type="file"
                id="file-input"
                className="form-input"
                onChange={handleFileChange}
                accept=".pdf,.txt,.doc,.docx,.md,.html"
                required
              />
              <div className="text-sm text-secondary mt-1">
                Supported formats: PDF, TXT, DOC, DOCX, MD, HTML
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="metadata" className="form-label">Metadata (Optional)</label>
              <textarea
                id="metadata"
                className="form-textarea"
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
                placeholder='{"source": "manual_upload", "category": "documentation", "tags": ["guide", "reference"]}'
                rows={4}
              />
              <div className="text-sm text-secondary mt-1">
                JSON format for additional document metadata
              </div>
            </div>

            <div className="flex gap-3">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading || !file}
              >
                {loading ? (
                  <>
                    <span className="loading"></span>
                    Uploading...
                  </>
                ) : (
                  'Upload Document'
                )}
              </button>

              <button 
                type="button" 
                className="btn btn-outline"
                onClick={clearForm}
                disabled={loading}
              >
                Clear Form
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📋 Upload Information</h3>
            <p className="card-subtitle">What happens when you upload a document</p>
          </div>

          <div>
            <h4>Processing Steps:</h4>
            <ol>
              <li><strong>File Validation:</strong> Check file format and size</li>
              <li><strong>Text Extraction:</strong> Extract text content from the document</li>
              <li><strong>Chunking:</strong> Split text into manageable chunks</li>
              <li><strong>Embedding:</strong> Generate vector embeddings for each chunk</li>
              <li><strong>Indexing:</strong> Store in vector database for retrieval</li>
              <li><strong>Metadata:</strong> Store document metadata and references</li>
            </ol>

            <h4 className="mt-4">Supported File Types:</h4>
            <ul>
              <li><strong>PDF:</strong> Text extraction from PDF documents</li>
              <li><strong>TXT:</strong> Plain text files</li>
              <li><strong>DOC/DOCX:</strong> Microsoft Word documents</li>
              <li><strong>MD:</strong> Markdown files</li>
              <li><strong>HTML:</strong> Web pages and HTML content</li>
            </ul>

            <h4 className="mt-4">File Size Limits:</h4>
            <p>Maximum file size: 50MB per document</p>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoint</h3>
          <p className="card-subtitle">Upload endpoint details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>POST /upload</h4>
            <p>Upload a document with optional metadata</p>
            <code className="block p-2 bg-gray-100 rounded text-sm">
              curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
                -F "file=@document.pdf" \
                -F 'metadata={{"source":"manual"}}' \
                http://localhost:8000/upload
            </code>
          </div>
          
          <div>
            <h4>Response</h4>
            <p>Returns upload confirmation and document ID</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              {`{
  "message": "Document uploaded successfully",
  "document_id": "doc_123",
  "filename": "document.pdf",
  "chunks_created": 15
}`}
            </pre>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">💡 Tips for Better Results</h3>
          <p className="card-subtitle">Optimize your document uploads</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>Document Quality:</h4>
            <ul>
              <li>Use high-quality, readable documents</li>
              <li>Ensure text is properly formatted</li>
              <li>Avoid heavily scanned or image-based PDFs</li>
              <li>Break large documents into smaller, focused files</li>
            </ul>
          </div>
          
          <div>
            <h4>Metadata Best Practices:</h4>
            <ul>
              <li>Add relevant tags and categories</li>
              <li>Include source information</li>
              <li>Specify document type and purpose</li>
              <li>Add creation or update dates</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Upload;


