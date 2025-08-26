import React, { useState, useEffect, useRef } from 'react'
import { 
  Send, 
  Download, 
  ExternalLink, 
  FileText, 
  MessageSquare,
  Bot,
  User,
  Copy,
  ChevronDown,
  ChevronUp,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { ragAPI, chatAPI } from '../services/api'
import { formatDate, copyToClipboard, isValidUrl } from '../lib/utils'
import { cn } from '../lib/utils'

export default function RagChat() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [expandedSources, setExpandedSources] = useState(new Set())
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await chatAPI.sendMessage([userMessage], conversationId)
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.message.content,
        sources: response.data.sources || [],
        timestamp: new Date().toISOString(),
        processingTime: response.data.processing_time
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationId(response.data.conversation_id)
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleSources = (messageId) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }

  const copyMessage = (content) => {
    copyToClipboard(content)
  }

  const showInTable = (sources) => {
    // This would highlight the relevant rows in the Data Explorer
    console.log('Show in table:', sources)
  }

  const MessageBubble = ({ message }) => {
    const isUser = message.role === 'user'
    const isExpanded = expandedSources.has(message.id)

    return (
      <div className={cn(
        "flex gap-3 mb-6",
        isUser ? "justify-end" : "justify-start"
      )}>
        {!isUser && (
          <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-primary-foreground" />
          </div>
        )}
        
        <div className={cn(
          "max-w-[80%] space-y-2",
          isUser ? "order-first" : "order-last"
        )}>
          <div className={cn(
            "rounded-lg p-4",
            isUser 
              ? "bg-primary text-primary-foreground" 
              : "bg-muted"
          )}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 whitespace-pre-wrap">{message.content}</div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyMessage(message.content)}
                  className="h-6 w-6 p-0"
                >
                  <Copy className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>

          {/* Message metadata */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatDate(message.timestamp)}</span>
            {message.processingTime && (
              <span>• {message.processingTime.toFixed(2)}s</span>
            )}
            {message.sources && message.sources.length > 0 && (
              <span>• {message.sources.length} sources</span>
            )}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => toggleSources(message.id)}
                  className="h-6 px-2"
                >
                  {isExpanded ? (
                    <ChevronUp className="w-3 h-3 mr-1" />
                  ) : (
                    <ChevronDown className="w-3 h-3 mr-1" />
                  )}
                  Sources ({message.sources.length})
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => showInTable(message.sources)}
                  className="h-6 px-2"
                >
                  <BarChart3 className="w-3 h-3 mr-1" />
                  Show in Table
                </Button>
              </div>

              {isExpanded && (
                <div className="space-y-2">
                  {message.sources.map((source, index) => (
                    <div key={index} className="bg-background border rounded-lg p-3">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm font-medium">{source.file_name}</span>
                          <Badge variant="outline" className="text-xs">
                            Score: {(source.similarity_score * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        {isValidUrl(source.document_id) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => window.open(source.document_id, '_blank')}
                            className="h-6 w-6 p-0"
                          >
                            <ExternalLink className="w-3 h-3" />
                          </Button>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {source.chunk_text.length > 200 
                          ? `${source.chunk_text.substring(0, 200)}...`
                          : source.chunk_text
                        }
                      </p>
                      {source.page_number && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Page {source.page_number}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {isUser && (
          <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">RAG Chat</h1>
          <p className="text-muted-foreground">
            Chat with your knowledge base using RAG-powered responses
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export Chat
          </Button>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Chat Panel */}
        <div className="flex-1 flex flex-col bg-card border rounded-lg">
          {/* Chat Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary" />
                <h2 className="font-semibold">Chat Conversation</h2>
                {conversationId && (
                  <Badge variant="outline" className="text-xs">
                    ID: {conversationId.slice(0, 8)}
                  </Badge>
                )}
              </div>
              <div className="text-sm text-muted-foreground">
                {messages.length} messages
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Bot className="w-12 h-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                <p className="text-muted-foreground max-w-md">
                  Ask questions about your uploaded documents and get intelligent answers 
                  powered by the RAG system with source citations.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            
            {isLoading && (
              <div className="flex gap-3 mb-6">
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-border">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your documents..."
                  className="w-full p-3 pr-12 border border-input rounded-lg resize-none bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                  rows={1}
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="px-4"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </div>

        {/* Right Sidebar - Sources Panel */}
        <div className="w-80 flex flex-col bg-card border rounded-lg">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold">Sources & References</h3>
            <p className="text-sm text-muted-foreground">
              View document sources and references
            </p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground">
                <FileText className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">Sources will appear here when you start chatting</p>
              </div>
            ) : (
              <div className="space-y-3">
                {messages
                  .filter(m => m.sources && m.sources.length > 0)
                  .map((message) => (
                    <div key={message.id} className="space-y-2">
                      <div className="text-xs font-medium text-muted-foreground">
                        {formatDate(message.timestamp)}
                      </div>
                      {message.sources.slice(0, 3).map((source, index) => (
                        <div key={index} className="bg-muted rounded p-2 text-xs">
                          <div className="font-medium">{source.file_name}</div>
                          <div className="text-muted-foreground">
                            Score: {(source.similarity_score * 100).toFixed(1)}%
                          </div>
                        </div>
                      ))}
                      {message.sources.length > 3 && (
                        <div className="text-xs text-muted-foreground">
                          +{message.sources.length - 3} more sources
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

