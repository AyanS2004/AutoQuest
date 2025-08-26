import React, { useState, useEffect } from 'react'
import { 
  Download, 
  Upload, 
  Activity,
  Database,
  FileText,
  AlertCircle,
  CheckCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Progress } from '../components/ui/Progress'
import { Badge } from '../components/ui/Badge'
import { healthAPI, documentsAPI } from '../services/api'
import { formatDate, formatNumber } from '../lib/utils'
import { cn } from '../lib/utils'

export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const [healthRes, docsRes] = await Promise.all([
          healthAPI.getHealth().catch(() => ({ data: null })),
          documentsAPI.list().catch(() => ({ data: [] }))
        ])
        setHealth(healthRes.data)
        setDocuments(docsRes.data || [])
      } catch (e) {
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
    const interval = setInterval(load, 30000)
    return () => clearInterval(interval)
  }, [])

  const status = health?.status || 'unknown'
  const uptimeSeconds = health?.uptime || 0
  const uptime = `${Math.floor(uptimeSeconds / 3600)}h ${Math.floor((uptimeSeconds % 3600) / 60)}m`
  const docCount = documents.length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">System overview and data status</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => window.location.reload()}>Refresh</Button>
          <Button variant="outline">
            <Upload className="w-4 h-4 mr-2" />
            Upload Data
          </Button>
        </div>
      </div>

      {error && (
        <Card>
          <CardContent>
            <div className="text-red-600 text-sm">{error}</div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{status}</div>
            <p className="text-xs text-muted-foreground">Uptime: {uptime}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(docCount)}</div>
            <p className="text-xs text-muted-foreground">In knowledge base</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Model</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {health?.model_status ? 'Available' : 'Unknown'}
            </div>
            <p className="text-xs text-muted-foreground">LLM + Vector DB connectivity</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(health?.memory_usage?.percent || 0)}%</div>
            <p className="text-xs text-muted-foreground">System memory usage</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <div className="text-sm text-muted-foreground">No documents found</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-2 text-left text-sm text-muted-foreground">File</th>
                    <th className="px-4 py-2 text-left text-sm text-muted-foreground">Type</th>
                    <th className="px-4 py-2 text-left text-sm text-muted-foreground">Chunks</th>
                    <th className="px-4 py-2 text-left text-sm text-muted-foreground">Uploaded</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.slice(0, 5).map((d) => (
                    <tr key={d.id} className="border-b border-border">
                      <td className="px-4 py-2 text-sm">{d.file_name}</td>
                      <td className="px-4 py-2 text-sm">{d.file_type}</td>
                      <td className="px-4 py-2 text-sm">{d.chunk_count}</td>
                      <td className="px-4 py-2 text-sm">{formatDate(d.upload_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
