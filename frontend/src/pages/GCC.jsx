import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { 
  Play, 
  Stop, 
  Download, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Settings
} from 'lucide-react';
import gccService from '../services/gccService';

const GCC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState({
    inputFile: 'solutions.xlsx',
    outputFile: 'solutions_processed.xlsx',
    templateFile: 'template.xlsx',
    debugPort: 9222
  });

  const [sessionInfo, setSessionInfo] = useState({
    sessionId: null,
    startTime: null,
    endTime: null,
    processedCompanies: 0,
    totalCompanies: 0,
    currentField: null
  });

  // Poll status updates when running
  useEffect(() => {
    if (isRunning && sessionInfo.sessionId) {
      const pollStatus = () => {
        gccService.pollStatus(
          sessionInfo.sessionId,
          (status) => {
            setStatus(status.status);
            if (status.status === 'completed' || status.status === 'failed') {
              setIsRunning(false);
              setProgress(100);
            } else if (status.status === 'running') {
              // Estimate progress based on processed companies
              const estimatedProgress = status.processed_companies && status.total_companies 
                ? (status.processed_companies / status.total_companies) * 100 
                : progress;
              setProgress(Math.min(estimatedProgress, 95)); // Cap at 95% until complete
            }
            
            // Update session info
            setSessionInfo(prev => ({
              ...prev,
              processedCompanies: status.processed_companies || 0,
              totalCompanies: status.total_companies || 0,
              currentField: status.current_field || null
            }));
            
            // Add log entry
            if (status.log_message) {
              addLog(status.log_message, status.log_level || 'info');
            }
          },
          (error) => {
            setError(error.message);
            setStatus('error');
            setIsRunning(false);
            addLog(`Error: ${error.message}`, 'error');
          }
        );
      };
      
      pollStatus();
    }
  }, [isRunning, sessionInfo.sessionId]);

  const startExtraction = async () => {
    try {
      setIsRunning(true);
      setStatus('starting');
      setProgress(0);
      setError(null);
      setLogs([]);

      // Add initial log
      addLog('Starting GCC extraction...', 'info');

      // Call the real API
      const data = await gccService.startExtraction(config);
      
      setSessionInfo(prev => ({
        ...prev,
        sessionId: data.session_id,
        startTime: new Date(),
        processedCompanies: 0,
        totalCompanies: 0
      }));

      setStatus('running');
      addLog('GCC extraction started successfully', 'success');

    } catch (err) {
      setError(err.message);
      setStatus('error');
      setIsRunning(false);
      addLog(`Error: ${err.message}`, 'error');
    }
  };

  const stopExtraction = async () => {
    try {
      setIsRunning(false);
      setStatus('stopping');
      addLog('Stopping GCC extraction...', 'warning');

      // Call the real API
      await gccService.stopExtraction(sessionInfo.sessionId);

      setStatus('stopped');
      addLog('GCC extraction stopped', 'info');

    } catch (err) {
      setError(err.message);
      addLog(`Error stopping: ${err.message}`, 'error');
    }
  };

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { message, type, timestamp }]);
  };

  const downloadResults = async () => {
    try {
      await gccService.downloadResults(config.outputFile);
      addLog('Results downloaded successfully', 'success');
    } catch (err) {
      setError(err.message);
      addLog(`Download failed: ${err.message}`, 'error');
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'completed': return 'bg-blue-500';
      case 'error': return 'bg-red-500';
      case 'stopped': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'running': return <Play className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      case 'stopped': return <Stop className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">GCC Extraction</h1>
          <p className="text-muted-foreground">
            Google Cloud Console data extraction tool
          </p>
        </div>
        <Badge className={`${getStatusColor()} text-white`}>
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            {status.toUpperCase()}
          </div>
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Configuration
            </CardTitle>
            <CardDescription>
              Configure your GCC extraction parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="inputFile">Input File</Label>
              <Input
                id="inputFile"
                value={config.inputFile}
                onChange={(e) => setConfig(prev => ({ ...prev, inputFile: e.target.value }))}
                disabled={isRunning}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="outputFile">Output File</Label>
              <Input
                id="outputFile"
                value={config.outputFile}
                onChange={(e) => setConfig(prev => ({ ...prev, outputFile: e.target.value }))}
                disabled={isRunning}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="templateFile">Template File</Label>
              <Input
                id="templateFile"
                value={config.templateFile}
                onChange={(e) => setConfig(prev => ({ ...prev, templateFile: e.target.value }))}
                disabled={isRunning}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="debugPort">Debug Port</Label>
              <Input
                id="debugPort"
                type="number"
                value={config.debugPort}
                onChange={(e) => setConfig(prev => ({ ...prev, debugPort: parseInt(e.target.value) }))}
                disabled={isRunning}
              />
            </div>
          </CardContent>
        </Card>

        {/* Session Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Session Information
            </CardTitle>
            <CardDescription>
              Current extraction session details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Session ID</Label>
                <p className="font-mono text-sm">{sessionInfo.sessionId || 'Not started'}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Progress</Label>
                <p className="font-semibold">{Math.round(progress)}%</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Processed</Label>
                <p className="font-semibold">{sessionInfo.processedCompanies} / {sessionInfo.totalCompanies}</p>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Current Field</Label>
                <p className="font-semibold">{sessionInfo.currentField || 'None'}</p>
              </div>
            </div>
            
            {isRunning && (
              <div className="space-y-2">
                <Label>Progress</Label>
                <Progress value={progress} className="w-full" />
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={startExtraction}
                disabled={isRunning}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Extraction
              </Button>
              <Button
                onClick={stopExtraction}
                disabled={!isRunning}
                variant="destructive"
                className="flex-1"
              >
                <Stop className="w-4 h-4 mr-2" />
                Stop
              </Button>
            </div>

            {status === 'completed' && (
              <Button
                onClick={downloadResults}
                className="w-full"
                variant="outline"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Results
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Logs Card */}
      <Card>
        <CardHeader>
          <CardTitle>Extraction Logs</CardTitle>
          <CardDescription>
            Real-time logs from the GCC extraction process
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 overflow-y-auto space-y-2 bg-gray-50 p-4 rounded-md">
            {logs.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No logs yet. Start an extraction to see logs here.
              </p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground min-w-[60px]">
                    {log.timestamp}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    log.type === 'error' ? 'bg-red-100 text-red-800' :
                    log.type === 'success' ? 'bg-green-100 text-green-800' :
                    log.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {log.type.toUpperCase()}
                  </span>
                  <span className="flex-1">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GCC;
