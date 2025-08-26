import React from 'react';
import { Link } from 'react-router-dom';

function App() {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">AutoQuest</h1>
        <p className="page-subtitle">
          Advanced RAG-powered document analysis and intelligent chat system
        </p>
      </div>

      <div className="grid grid-3">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Authentication</h3>
            <p className="card-subtitle">Get your JWT token to access the API</p>
          </div>
          <p>
            Start by obtaining an authentication token to interact with the AutoQuest API.
            This token will be stored locally and used for all subsequent requests.
          </p>
          <Link to="/token" className="btn btn-primary">
            Get Token
          </Link>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📊 System Health</h3>
            <p className="card-subtitle">Check the status of all services</p>
          </div>
          <p>
            Monitor the health of the backend services including the RAG engine,
            vector database, and external dependencies.
          </p>
          <Link to="/health" className="btn btn-secondary">
            Check Health
          </Link>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📁 Document Upload</h3>
            <p className="card-subtitle">Add documents to your knowledge base</p>
          </div>
          <p>
            Upload PDFs, text files, and other documents to build your knowledge base.
            Documents are processed and indexed for intelligent retrieval.
          </p>
          <Link to="/upload" className="btn btn-success">
            Upload Documents
          </Link>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">❓ Ask Questions</h3>
            <p className="card-subtitle">Query your knowledge base</p>
          </div>
          <p>
            Ask questions about your uploaded documents and get intelligent answers
            powered by the RAG system with source citations.
          </p>
          <Link to="/ask" className="btn btn-primary">
            Ask Questions
          </Link>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📚 Document Library</h3>
            <p className="card-subtitle">View all uploaded documents</p>
          </div>
          <p>
            Browse through all documents in your knowledge base, view metadata,
            and manage your document collection.
          </p>
          <Link to="/documents" className="btn btn-outline">
            View Documents
          </Link>
        </div>

                 <div className="card">
           <div className="card-header">
             <h3 className="card-title">💬 Interactive Chat</h3>
             <p className="card-subtitle">Have a conversation with your data</p>
           </div>
           <p>
             Engage in a conversational interface with your knowledge base.
             Maintain context across multiple questions and explore your data naturally.
           </p>
           <Link to="/chat" className="btn btn-primary">
             Start Chat
           </Link>
         </div>

         <div className="card">
           <div className="card-header">
             <h3 className="card-title">🔍 Company Research</h3>
             <p className="card-subtitle">Automated research with Selenium</p>
           </div>
           <p>
             Excel-like interface for entering companies and research fields.
             Uses Selenium automation to gather data and generate Excel files for RAG analysis.
           </p>
           <Link to="/research" className="btn btn-success">
             Start Research
           </Link>
         </div>

         <div className="card">
           <div className="card-header">
             <h3 className="card-title">☁️ GCC Extraction</h3>
             <p className="card-subtitle">Google Cloud Console data extraction</p>
           </div>
           <p>
             Automated extraction of data from Google Cloud Console.
             Configure input files, monitor progress, and download results through a web interface.
           </p>
           <Link to="/gcc" className="btn btn-warning">
             Start GCC Extraction
           </Link>
         </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">🚀 Getting Started</h3>
          <p className="card-subtitle">Quick setup guide</p>
        </div>
        <div className="grid grid-2">
          <div>
            <h4>1. Authentication</h4>
            <p>First, get your API token from the Auth page to enable all features.</p>
            
            <h4>2. Upload Documents</h4>
            <p>Add your documents to build a knowledge base for intelligent queries.</p>
            
            <h4>3. Start Exploring</h4>
            <p>Use the Ask or Chat features to interact with your uploaded documents.</p>
          </div>
          <div>
            <h4>🔧 Features</h4>
            <ul>
              <li>Advanced RAG (Retrieval-Augmented Generation)</li>
              <li>Multiple vector database support</li>
              <li>Document processing and indexing</li>
              <li>Intelligent question answering</li>
              <li>Conversational chat interface</li>
              <li>Source citation and references</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;


