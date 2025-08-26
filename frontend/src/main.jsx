import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';

// Import layout and pages
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataExplorer from './pages/DataExplorer';
import RagChat from './pages/RagChat';
import Logs from './pages/Logs';

// Import existing pages (keeping for compatibility)
import App from './pages/App';
import Token from './pages/Token';
import Health from './pages/Health';
import Upload from './pages/Upload';
import Ask from './pages/Ask';
import Documents from './pages/Documents';
import Chat from './pages/Chat';
import Research from './pages/Research';

// Main App component
function AppWrapper() {
  return (
    <Router>
      <Routes>
        {/* Dashboard routes with new layout */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="explorer" element={<DataExplorer />} />
          <Route path="rag-chat" element={<RagChat />} />
          <Route path="logs" element={<Logs />} />
        </Route>

        {/* Legacy routes (keeping for compatibility) */}
        <Route path="/legacy" element={<App />} />
        <Route path="/token" element={<Token />} />
        <Route path="/health" element={<Health />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/research" element={<Research />} />
      </Routes>
    </Router>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppWrapper />
  </React.StrictMode>
);


