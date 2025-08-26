import React, { useState, useEffect } from 'react'
import { 
  Search, 
  Download, 
  Edit, 
  Save, 
  X,
  ExternalLink
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { documentsAPI, dataAPI } from '../services/api'
import { formatDate } from '../lib/utils'
import { cn } from '../lib/utils'

export default function DataExplorer() {
  const [rows, setRows] = useState([])
  const [filtered, setFiltered] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  const columns = [
    { key: 'file_name', label: 'File Name', sortable: true },
    { key: 'file_type', label: 'Type', sortable: true },
    { key: 'chunk_count', label: 'Chunks', sortable: true },
    { key: 'upload_date', label: 'Uploaded', sortable: true },
    { key: 'actions', label: 'Actions', sortable: false }
  ]

  useEffect(() => {
    load()
  }, [])

  useEffect(() => {
    filterAndSort()
  }, [rows, searchTerm, sortConfig])

  const load = async () => {
    try {
      setLoading(true)
      const res = await documentsAPI.list()
      setRows(res.data || [])
    } catch (e) {
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  const filterAndSort = () => {
    let data = rows.filter(r =>
      r.file_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.file_type?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    if (sortConfig.key) {
      data.sort((a, b) => {
        const aVal = a[sortConfig.key]
        const bVal = b[sortConfig.key]
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
        return 0
      })
    }
    setFiltered(data)
  }

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  const exportCSV = () => {
    const header = ['file_name', 'file_type', 'chunk_count', 'upload_date']
    const csv = [header.join(',')]
    filtered.forEach(r => {
      csv.push([
        r.file_name,
        r.file_type,
        r.chunk_count,
        r.upload_date
      ].join(','))
    })
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `documents_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Explorer</h1>
          <p className="text-muted-foreground">Browse processed documents</p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={exportCSV}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background"
              />
            </div>
            <Button variant="outline" onClick={load}>Refresh</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Documents ({filtered.length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  {columns.map(col => (
                    <th
                      key={col.key}
                      className={cn('px-4 py-3 text-left text-sm font-medium text-muted-foreground', col.sortable && 'cursor-pointer hover:bg-muted')}
                      onClick={() => col.sortable && handleSort(col.key)}
                    >
                      <div className="flex items-center gap-1">
                        <span>{col.label}</span>
                        {col.sortable && sortConfig.key === col.key && (
                          <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td className="px-4 py-6 text-sm" colSpan={columns.length}>Loading...</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td className="px-4 py-6 text-sm" colSpan={columns.length}>No data</td></tr>
                ) : (
                  filtered.map((r) => (
                    <tr key={r.id} className="border-b border-border hover:bg-muted/50">
                      <td className="px-4 py-3 text-sm">{r.file_name}</td>
                      <td className="px-4 py-3 text-sm">{r.file_type}</td>
                      <td className="px-4 py-3 text-sm">{r.chunk_count}</td>
                      <td className="px-4 py-3 text-sm">{formatDate(r.upload_date)}</td>
                      <td className="px-4 py-3 text-sm">
                        <Button variant="ghost" size="sm" onClick={() => {}}>
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
