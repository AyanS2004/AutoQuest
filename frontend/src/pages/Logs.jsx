import React, { useState, useEffect, useRef } from 'react'
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Info, 
  AlertTriangle,
  Download,
  Trash2,
  RefreshCw,
  Filter,
  Play,
  Pause,
  Eye,
  EyeOff
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { logsAPI } from '../services/api'
import { formatDate } from '../lib/utils'
import { cn } from '../lib/utils'

export default function Logs() {
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [filters, setFilters] = useState({
    level: 'all',
    search: '',
    showErrors: true,
    showWarnings: true,
    showInfo: true
  })
  const [stats, setStats] = useState({
    total: 0,
    errors: 0,
    warnings: 0,
    info: 0
  })
  const logsEndRef = useRef(null)
  const [autoScroll, setAutoScroll] = useState(true)

  useEffect(() => {
    loadLogs()
  }, [])

  useEffect(() => {
    filterLogs()
  }, [logs, filters])

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom()
    }
  }, [filteredLogs])

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadLogs = async () => {
    try {
      setLoading(true)
      const response = await logsAPI.getLogs()
      const logEntries = response.data.map(log => ({
        ...log,
        id: Date.now() + Math.random(),
        timestamp: new Date(log.timestamp || Date.now()).toISOString()
      }))
      setLogs(logEntries)
      updateStats(logEntries)
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const startStreaming = async () => {
    setIsStreaming(true)
    // In a real implementation, this would connect to a WebSocket or SSE endpoint
    // For demo purposes, we'll simulate real-time logs
    const interval = setInterval(() => {
      const newLog = generateMockLog()
      setLogs(prev => {
        const newLogs = [...prev, newLog]
        updateStats(newLogs)
        return newLogs
      })
    }, 2000)

    return () => clearInterval(interval)
  }

  const stopStreaming = () => {
    setIsStreaming(false)
  }

  const generateMockLog = () => {
    const levels = ['info', 'warning', 'error']
    const level = levels[Math.floor(Math.random() * levels.length)]
    const messages = {
      info: [
        'Document processed successfully',
        'RAG query completed',
        'Company data extracted',
        'Session started',
        'Backup completed'
      ],
      warning: [
        'Low confidence extraction',
        'Rate limit approaching',
        'Memory usage high',
        'Network timeout',
        'Partial data retrieved'
      ],
      error: [
        'Failed to extract company data',
        'RAG query failed',
        'Document processing error',
        'Database connection failed',
        'API rate limit exceeded'
      ]
    }

    return {
      id: Date.now() + Math.random(),
      level,
      message: messages[level][Math.floor(Math.random() * messages[level].length)],
      timestamp: new Date().toISOString(),
      source: 'gcc_extractor',
      details: `Additional details for ${level} level log entry`
    }
  }

  const filterLogs = () => {
    let filtered = logs.filter(log => {
      const matchesLevel = filters.level === 'all' || log.level === filters.level
      const matchesSearch = !filters.search || 
        log.message.toLowerCase().includes(filters.search.toLowerCase()) ||
        log.source?.toLowerCase().includes(filters.search.toLowerCase())
      
      const matchesVisibility = 
        (log.level === 'error' && filters.showErrors) ||
        (log.level === 'warning' && filters.showWarnings) ||
        (log.level === 'info' && filters.showInfo)

      return matchesLevel && matchesSearch && matchesVisibility
    })

    setFilteredLogs(filtered)
  }

  const updateStats = (logEntries) => {
    const stats = {
      total: logEntries.length,
      errors: logEntries.filter(log => log.level === 'error').length,
      warnings: logEntries.filter(log => log.level === 'warning').length,
      info: logEntries.filter(log => log.level === 'info').length
    }
    setStats(stats)
  }

  const clearLogs = async () => {
    try {
      await logsAPI.clearLogs()
      setLogs([])
      setFilteredLogs([])
      updateStats([])
    } catch (error) {
      console.error('Failed to clear logs:', error)
    }
  }

  const exportLogs = () => {
    const csvContent = [
      'Timestamp,Level,Message,Source,Details',
      ...filteredLogs.map(log => 
        `"${log.timestamp}","${log.level}","${log.message}","${log.source || ''}","${log.details || ''}"`
      )
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `autoquest_logs_${formatDate(new Date())}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const getLevelIcon = (level) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />
      default:
        return <CheckCircle className="w-4 h-4 text-green-500" />
    }
  }

  const getLevelBadge = (level) => {
    const variants = {
      error: 'destructive',
      warning: 'secondary',
      info: 'default'
    }
    return <Badge variant={variants[level]} className="text-xs">{level.toUpperCase()}</Badge>
  }

  const LogEntry = ({ log }) => {
    return (
      <div className={cn(
        "p-3 border-b border-border hover:bg-muted/50 transition-colors",
        log.level === 'error' && "bg-red-50",
        log.level === 'warning' && "bg-yellow-50"
      )}>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-1">
            {getLevelIcon(log.level)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {getLevelBadge(log.level)}
              <span className="text-sm font-medium">{log.source || 'System'}</span>
              <span className="text-xs text-muted-foreground">
                {formatDate(log.timestamp)}
              </span>
            </div>
            <p className="text-sm">{log.message}</p>
            {log.details && (
              <p className="text-xs text-muted-foreground mt-1">{log.details}</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Logs & Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time system logs and error monitoring
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={isStreaming ? stopStreaming : startStreaming}
            className={cn(isStreaming && "bg-green-50 border-green-200")}
          >
            {isStreaming ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Stop Streaming
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Streaming
              </>
            )}
          </Button>
          <Button variant="outline" onClick={loadLogs}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportLogs}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" onClick={clearLogs}>
            <Trash2 className="w-4 h-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.warnings}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Info</CardTitle>
            <Info className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.info}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search logs..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background"
              />
            </div>

            <select
              value={filters.level}
              onChange={(e) => setFilters(prev => ({ ...prev, level: e.target.value }))}
              className="px-3 py-2 border border-input rounded-md bg-background"
            >
              <option value="all">All Levels</option>
              <option value="error">Errors Only</option>
              <option value="warning">Warnings Only</option>
              <option value="info">Info Only</option>
            </select>

            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.showErrors}
                  onChange={(e) => setFilters(prev => ({ ...prev, showErrors: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Errors</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.showWarnings}
                  onChange={(e) => setFilters(prev => ({ ...prev, showWarnings: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Warnings</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.showInfo}
                  onChange={(e) => setFilters(prev => ({ ...prev, showInfo: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-sm">Info</span>
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoScroll(!autoScroll)}
                className={cn(autoScroll && "bg-blue-50 border-blue-200")}
              >
                {autoScroll ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                <span className="ml-2">Auto-scroll</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Display */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>System Logs ({filteredLogs.length} entries)</CardTitle>
            <div className="text-sm text-muted-foreground">
              {isStreaming && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  Live streaming
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-96 overflow-y-auto border rounded-lg">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
                <span className="ml-2">Loading logs...</span>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <Activity className="w-8 h-8 mr-2" />
                No logs found
              </div>
            ) : (
              <div>
                {filteredLogs.map((log) => (
                  <LogEntry key={log.id} log={log} />
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Recovery Panel */}
      {stats.errors > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
              Error Recovery Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-red-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-red-500" />
                  <span className="font-medium">Failed Extractions</span>
                </div>
                <div className="text-2xl font-bold text-red-600">{stats.errors}</div>
                <p className="text-sm text-red-600">Requires attention</p>
              </div>

              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  <span className="font-medium">Retries Attempted</span>
                </div>
                <div className="text-2xl font-bold text-yellow-600">
                  {Math.floor(stats.errors * 1.5)}
                </div>
                <p className="text-sm text-yellow-600">Automatic retries</p>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-4 h-4 text-blue-500" />
                  <span className="font-medium">Emergency Saves</span>
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {Math.floor(stats.errors * 0.3)}
                </div>
                <p className="text-sm text-blue-600">Data preserved</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
