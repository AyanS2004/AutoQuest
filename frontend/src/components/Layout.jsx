import React, { useState, useEffect } from 'react'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { 
  BarChart3, 
  Database, 
  MessageSquare, 
  FileText, 
  Settings, 
  Activity,
  Menu,
  X,
  Home,
  Search,
  Download,
  Upload
} from 'lucide-react'
import { cn } from '../lib/utils'
import { healthAPI } from '../services/api'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/explorer', label: 'Data Explorer', icon: Database },
  { path: '/rag-chat', label: 'RAG Chat', icon: MessageSquare },
  { path: '/documents', label: 'Documents', icon: FileText },
  { path: '/research', label: 'Research', icon: Search },
  { path: '/logs', label: 'Logs', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout() {
  const location = useLocation()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [systemStatus, setSystemStatus] = useState({
    status: 'unknown',
    uptime: 0,
    memory_usage: {},
    model_status: {}
  })

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await healthAPI.getHealth()
        setSystemStatus(response.data)
      } catch (error) {
        // keep minimal UI if health endpoint not ready
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500'
      case 'warning':
        return 'text-yellow-500'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <div className={cn(
      // Reserve space for fixed sidebar on large screens
      'min-h-screen bg-background lg:pl-64',
      // When sidebar hidden on mobile, remove padding
      !isSidebarOpen && 'pl-0'
    )}>
      {/* Sidebar (fixed) */}
      <div className={cn(
        'sidebar transition-transform duration-300 ease-in-out lg:translate-x-0',
        !isSidebarOpen && 'translate-x-[-100%]'
      )}>
        <div className="sidebar-content">
          {/* Logo */}
          <div className="flex items-center justify-between mb-8">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">AutoQuest</span>
            </Link>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-accent"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="sidebar-nav">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn('sidebar-nav-item', isActive && 'active')}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.label}
                </Link>
              )
            })}
          </nav>

          {/* System Status */}
          <div className="mt-8 p-4 bg-muted rounded-lg">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">System Status</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span>Status:</span>
                <span className={cn('flex items-center', getStatusColor(systemStatus.status))}>
                  <div className={cn(
                    'w-2 h-2 rounded-full mr-1',
                    systemStatus.status === 'healthy' && 'bg-green-500',
                    systemStatus.status === 'warning' && 'bg-yellow-500',
                    systemStatus.status === 'error' && 'bg-red-500',
                    (!systemStatus.status || systemStatus.status === 'unknown') && 'bg-gray-500'
                  )} />
                  {systemStatus.status || 'unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span>Uptime:</span>
                <span>{Math.floor((systemStatus.uptime || 0) / 3600)}h {Math.floor(((systemStatus.uptime || 0) % 3600) / 60)}m</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Bar */}
      <header className="h-16 border-b border-border bg-card flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden p-2 rounded-md hover:bg-accent"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold">
            {navItems.find(item => item.path === location.pathname)?.label || 'AutoQuest'}
          </h1>
        </div>

        <div className="flex items-center space-x-2">
          <button className="btn btn-outline btn-sm">
            <Upload className="w-4 h-4 mr-1" />
            Upload
          </button>
          <button className="btn btn-outline btn-sm">
            <Download className="w-4 h-4 mr-1" />
            Export
          </button>
        </div>
      </header>

      {/* Page Content */}
      <main className="min-h-[calc(100vh-4rem)]">
        <div className="p-4 sm:p-6">
          <Outlet />
        </div>
      </main>

      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </div>
  )
}
