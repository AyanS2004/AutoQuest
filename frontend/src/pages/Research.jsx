import React, { useState, useRef } from 'react';
import axios from 'axios';

function Research() {
  const [companies, setCompanies] = useState([
    { id: 1, name: '', industry: '', website: '', researchFields: '', status: 'pending' }
  ]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [researchProgress, setResearchProgress] = useState(null);
  const [excelFile, setExcelFile] = useState(null);

  const addCompany = () => {
    const newId = companies.length > 0 ? Math.max(...companies.map(c => c.id)) + 1 : 1;
    setCompanies([...companies, { 
      id: newId, 
      name: '', 
      industry: '', 
      website: '', 
      researchFields: '', 
      status: 'pending' 
    }]);
  };

  const removeCompany = (id) => {
    setCompanies(companies.filter(company => company.id !== id));
  };

  const updateCompany = (id, field, value) => {
    setCompanies(companies.map(company => 
      company.id === id ? { ...company, [field]: value } : company
    ));
  };

  const validateCompanies = () => {
    const validCompanies = companies.filter(company => 
      company.name.trim() && company.researchFields.trim()
    );
    
    if (validCompanies.length === 0) {
      setMessage('Please add at least one company with a name and research fields.');
      setMessageType('error');
      return false;
    }
    
    return true;
  };

  const startResearch = async () => {
    if (!validateCompanies()) return;

    setLoading(true);
    setMessage('');
    setResearchProgress({ current: 0, total: companies.length, status: 'Starting research...' });

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setMessage('No authentication token found. Please get a token first.');
        setMessageType('error');
        return;
      }

      const validCompanies = companies.filter(company => 
        company.name.trim() && company.researchFields.trim()
      );

      // Start the research process
      const response = await axios.post('http://localhost:8000/research/start', {
        companies: validCompanies.map(company => ({
          name: company.name.trim(),
          industry: company.industry.trim(),
          website: company.website.trim(),
          research_fields: company.researchFields.trim().split(',').map(field => field.trim())
        }))
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      setMessage('Research started successfully! The system will now gather data using Selenium automation.');
      setMessageType('success');

      // Poll for progress updates
      pollResearchProgress(response.data.research_id);

    } catch (error) {
      console.error('Error starting research:', error);
      setMessage(error.response?.data?.detail || 'Failed to start research');
      setMessageType('error');
      setLoading(false);
    }
  };

  const pollResearchProgress = async (researchId) => {
    const token = localStorage.getItem('token');
    
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/research/status/${researchId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        const progress = response.data;
        setResearchProgress(progress);

        if (progress.status === 'completed') {
          clearInterval(pollInterval);
          setLoading(false);
          setMessage('Research completed! Excel file has been generated and uploaded to RAG system.');
          setMessageType('success');
          setExcelFile(progress.excel_file);
        } else if (progress.status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
          setMessage('Research failed. Please check the logs for details.');
          setMessageType('error');
        }
      } catch (error) {
        console.error('Error polling progress:', error);
      }
    }, 5000); // Poll every 5 seconds
  };

  const downloadExcel = () => {
    if (excelFile) {
      window.open(`http://localhost:8000/research/download/${excelFile}`, '_blank');
    }
  };

  const clearResearch = () => {
    setCompanies([{ id: 1, name: '', industry: '', website: '', researchFields: '', status: 'pending' }]);
    setMessage('');
    setResearchProgress(null);
    setExcelFile(null);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Company Research</h1>
        <p className="page-subtitle">Excel-like interface for automated company research using Selenium</p>
      </div>

      {message && (
        <div className={`alert alert-${messageType}`}>
          {message}
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="card-title">📊 Research Table</h3>
              <p className="card-subtitle">Enter companies and research fields</p>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={addCompany}
                className="btn btn-secondary btn-sm"
                disabled={loading}
              >
                + Add Company
              </button>
              <button 
                onClick={clearResearch}
                className="btn btn-outline btn-sm"
                disabled={loading}
              >
                Clear All
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="research-table">
            <thead>
              <tr>
                <th>Company Name *</th>
                <th>Industry</th>
                <th>Website</th>
                <th>Research Fields *</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((company) => (
                <tr key={company.id}>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      value={company.name}
                      onChange={(e) => updateCompany(company.id, 'name', e.target.value)}
                      placeholder="e.g., Apple Inc."
                      disabled={loading}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      value={company.industry}
                      onChange={(e) => updateCompany(company.id, 'industry', e.target.value)}
                      placeholder="e.g., Technology"
                      disabled={loading}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      value={company.website}
                      onChange={(e) => updateCompany(company.id, 'website', e.target.value)}
                      placeholder="e.g., https://apple.com"
                      disabled={loading}
                    />
                  </td>
                  <td>
                    <input
                      type="text"
                      className="form-input"
                      value={company.researchFields}
                      onChange={(e) => updateCompany(company.id, 'researchFields', e.target.value)}
                      placeholder="e.g., financial performance, market share, competitors"
                      disabled={loading}
                    />
                  </td>
                  <td>
                    <span className={`status-badge status-${company.status}`}>
                      {company.status}
                    </span>
                  </td>
                  <td>
                    {companies.length > 1 && (
                      <button
                        onClick={() => removeCompany(company.id)}
                        className="btn btn-danger btn-sm"
                        disabled={loading}
                      >
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex gap-3">
          <button 
            onClick={startResearch}
            className="btn btn-primary"
            disabled={loading || companies.length === 0}
          >
            {loading ? (
              <>
                <span className="loading"></span>
                Researching...
              </>
            ) : (
              '🚀 Start Research'
            )}
          </button>

          {excelFile && (
            <button 
              onClick={downloadExcel}
              className="btn btn-success"
            >
              📥 Download Excel
            </button>
          )}
        </div>
      </div>

      {researchProgress && (
        <div className="card mt-5">
          <div className="card-header">
            <h3 className="card-title">📈 Research Progress</h3>
            <p className="card-subtitle">Current status of automated research</p>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="font-medium">Status:</span>
              <span className={`status-badge status-${researchProgress.status}`}>
                {researchProgress.status}
              </span>
            </div>

            {researchProgress.current > 0 && (
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">Progress:</span>
                  <span>{researchProgress.current} / {researchProgress.total} companies</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(researchProgress.current / researchProgress.total) * 100}%` }}
                  ></div>
                </div>
              </div>
            )}

            {researchProgress.current_company && (
              <div className="bg-gray-50 p-3 rounded">
                <span className="font-medium">Currently researching:</span> {researchProgress.current_company}
              </div>
            )}

            {researchProgress.logs && researchProgress.logs.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recent Activity:</h4>
                <div className="bg-gray-50 p-3 rounded max-h-32 overflow-y-auto">
                  {researchProgress.logs.slice(-5).map((log, index) => (
                    <div key={index} className="text-sm text-gray-600 mb-1">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-2 mt-5">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🔍 How It Works</h3>
            <p className="card-subtitle">Automated research process</p>
          </div>

          <div>
            <h4>Research Process:</h4>
            <ol>
              <li><strong>Data Entry:</strong> Enter companies and research fields</li>
              <li><strong>Selenium Automation:</strong> Automated web scraping and data collection</li>
              <li><strong>Excel Generation:</strong> Compile research data into Excel format</li>
              <li><strong>RAG Integration:</strong> Upload Excel to knowledge base</li>
              <li><strong>Chat Analysis:</strong> Ask questions about the research data</li>
            </ol>

            <h4 className="mt-4">Research Fields Examples:</h4>
            <ul>
              <li>Financial performance, revenue, profit margins</li>
              <li>Market share, competitors, industry position</li>
              <li>Product portfolio, services, technology stack</li>
              <li>Leadership team, company history, recent news</li>
              <li>Customer reviews, ratings, social media presence</li>
            </ul>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💡 Tips for Better Research</h3>
            <p className="card-subtitle">Optimize your research results</p>
          </div>

          <div>
            <h4>Best Practices:</h4>
            <ul>
              <li>Use specific, focused research fields</li>
              <li>Include company websites when available</li>
              <li>Group similar companies for comparison</li>
              <li>Be patient - research takes time</li>
              <li>Check the Chat page to analyze results</li>
            </ul>

            <h4 className="mt-4">After Research:</h4>
            <ul>
              <li>Download the Excel file for manual review</li>
              <li>Use the Chat interface to ask questions</li>
              <li>Compare companies using natural language</li>
              <li>Generate insights and summaries</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="card mt-5">
        <div className="card-header">
          <h3 className="card-title">📋 API Endpoints</h3>
          <p className="card-subtitle">Research API details</p>
        </div>
        
        <div className="grid grid-2">
          <div>
            <h4>POST /research/start</h4>
            <p>Start automated research for companies</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">{`curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"companies": [{"name": "Apple", "research_fields": ["financial", "market"]}]}' \
  http://localhost:8000/research/start`}
            </pre>
          </div>
          
          <div>
            <h4>GET /research/status/{'{research_id}'}</h4>
            <p>Check research progress and status</p>
            <pre className="block p-2 bg-gray-100 rounded text-sm">
              curl -H "Authorization: Bearer YOUR_TOKEN" \
                http://localhost:8000/research/status/123
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Research;

