'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Folder,
  FolderOpen, 
  File,
  Code2,
  FileText,
  Settings,
  TestTube,
  Image,
  Database,
  FileCode,
  Search,
  Filter,
  Download,
  Eye,
  GitBranch,
  Clock,
  User,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Copy,
  Check,
  Maximize2,
  X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

// Types
interface CodeArtifact {
  id: string
  project_id: string
  agent_id: string
  agent_name: string
  file_path: string
  file_name: string
  artifact_type: string
  content: string
  content_hash: string
  status: string
  version: number
  description: string
  created_at: string
  updated_at: string
  reviewed_by?: string
}

interface FileTreeNode {
  name: string
  type: 'file' | 'directory'
  path: string
  children?: FileTreeNode[]
  artifact?: CodeArtifact
}

interface CodebaseExplorerProps {
  projectId: string
  projectName: string
}

export function CodebaseExplorer({ projectId, projectName }: CodebaseExplorerProps) {
  const [artifacts, setArtifacts] = useState<CodeArtifact[]>([])
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([])
  const [selectedFile, setSelectedFile] = useState<CodeArtifact | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [agentFilter, setAgentFilter] = useState<string>('all')
  const [loading, setLoading] = useState(true)
  const [showFileViewer, setShowFileViewer] = useState(false)
  const [copied, setCopied] = useState(false)

  // Fetch artifacts from API
  useEffect(() => {
    const fetchArtifacts = async () => {
      try {
        setLoading(true)
        const response = await fetch(`/api/v1/artifacts/project/${projectId}`)
        if (response.ok) {
          const data = await response.json()
          setArtifacts(data.artifacts || [])
          buildFileTree(data.artifacts || [])
        }
      } catch (error) {
        console.error('Failed to fetch artifacts:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchArtifacts()
  }, [projectId])

  // Build file tree from artifacts
  const buildFileTree = (artifacts: CodeArtifact[]) => {
    const tree: FileTreeNode[] = []
    const folderMap = new Map<string, FileTreeNode>()

    artifacts.forEach(artifact => {
      const pathParts = artifact.file_path.split('/')
      let currentPath = ''
      let currentLevel = tree

      pathParts.forEach((part, index) => {
        const isFile = index === pathParts.length - 1
        currentPath = currentPath ? `${currentPath}/${part}` : part

        if (isFile) {
          // Add file node
          currentLevel.push({
            name: part,
            type: 'file',
            path: currentPath,
            artifact
          })
        } else {
          // Add or find directory node
          let dirNode = currentLevel.find(node => node.name === part && node.type === 'directory')
          
          if (!dirNode) {
            dirNode = {
              name: part,
              type: 'directory',
              path: currentPath,
              children: []
            }
            currentLevel.push(dirNode)
            folderMap.set(currentPath, dirNode)
          }
          
          currentLevel = dirNode.children!
        }
      })
    })

    // Sort tree - directories first, then files
    const sortTree = (nodes: FileTreeNode[]): FileTreeNode[] => {
      return nodes.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      }).map(node => ({
        ...node,
        children: node.children ? sortTree(node.children) : undefined
      }))
    }

    setFileTree(sortTree(tree))
  }

  // Filter artifacts based on search and filters
  const filteredArtifacts = artifacts.filter(artifact => {
    const matchesSearch = !searchQuery || 
      artifact.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      artifact.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      artifact.content.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesStatus = statusFilter === 'all' || artifact.status === statusFilter
    const matchesAgent = agentFilter === 'all' || artifact.agent_id === agentFilter
    
    return matchesSearch && matchesStatus && matchesAgent
  })

  // Get unique agents for filter
  const uniqueAgents = Array.from(new Set(artifacts.map(a => a.agent_id)))
    .map(agentId => {
      const artifact = artifacts.find(a => a.agent_id === agentId)
      return { id: agentId, name: artifact?.agent_name || agentId }
    })

  // Toggle folder expansion
  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFolders(newExpanded)
  }

  // Get file icon based on type
  const getFileIcon = (fileName: string, artifactType: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    
    if (artifactType === 'configuration') return <Settings className="h-4 w-4 text-orange-500" />
    if (artifactType === 'test_file') return <TestTube className="h-4 w-4 text-green-500" />
    if (artifactType === 'documentation') return <FileText className="h-4 w-4 text-blue-500" />
    if (artifactType === 'schema') return <Database className="h-4 w-4 text-purple-500" />
    
    switch (ext) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
        return <FileCode className="h-4 w-4 text-yellow-500" />
      case 'py':
        return <FileCode className="h-4 w-4 text-blue-500" />
      case 'java':
        return <FileCode className="h-4 w-4 text-orange-500" />
      case 'css':
      case 'scss':
        return <FileCode className="h-4 w-4 text-pink-500" />
      case 'html':
        return <FileCode className="h-4 w-4 text-red-500" />
      case 'json':
        return <FileCode className="h-4 w-4 text-green-500" />
      case 'md':
        return <FileText className="h-4 w-4 text-blue-500" />
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'svg':
        return <Image className="h-4 w-4 text-purple-500" />
      default:
        return <File className="h-4 w-4 text-gray-500" />
    }
  }

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'bg-green-500'
      case 'deployed': return 'bg-blue-500'
      case 'review_pending': return 'bg-yellow-500'
      case 'draft': return 'bg-gray-500'
      case 'archived': return 'bg-gray-400'
      default: return 'bg-gray-500'
    }
  }

  // Copy file content to clipboard
  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy content:', err)
    }
  }

  // Render file tree node
  const renderTreeNode = (node: FileTreeNode, depth = 0) => {
    const isExpanded = expandedFolders.has(node.path)
    const isSelected = selectedFile?.id === node.artifact?.id

    return (
      <div key={node.path}>
        <motion.div
          className={cn(
            "flex items-center gap-2 py-1 px-2 rounded cursor-pointer hover:bg-muted/50 transition-colors",
            isSelected && "bg-primary/20",
            depth > 0 && "ml-4"
          )}
          onClick={() => {
            if (node.type === 'directory') {
              toggleFolder(node.path)
            } else if (node.artifact) {
              setSelectedFile(node.artifact)
            }
          }}
          whileHover={{ x: 2 }}
        >
          {node.type === 'directory' ? (
            <>
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              {isExpanded ? (
                <FolderOpen className="h-4 w-4 text-blue-500" />
              ) : (
                <Folder className="h-4 w-4 text-blue-500" />
              )}
            </>
          ) : (
            <>
              <div className="w-4" />
              {getFileIcon(node.name, node.artifact?.artifact_type || 'source_code')}
            </>
          )}
          
          <span className="text-sm truncate flex-1">{node.name}</span>
          
          {node.artifact && (
            <div className="flex items-center gap-1">
              <div className={cn(
                "w-2 h-2 rounded-full",
                getStatusColor(node.artifact.status)
              )} />
              <span className="text-xs text-muted-foreground">v{node.artifact.version}</span>
            </div>
          )}
        </motion.div>

        <AnimatePresence>
          {node.type === 'directory' && isExpanded && node.children && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              {node.children.map(child => renderTreeNode(child, depth + 1))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">{projectName} Codebase</h2>
            <p className="text-sm text-muted-foreground">
              {artifacts.length} files • {uniqueAgents.length} agents
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <GitBranch className="h-4 w-4 mr-2" />
              Branches
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="review_pending">Review</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="deployed">Deployed</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>

          <Select value={agentFilter} onValueChange={setAgentFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Agent" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Agents</SelectItem>
              {uniqueAgents.map(agent => (
                <SelectItem key={agent.id} value={agent.id}>
                  {agent.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* File Tree */}
        <div className="w-80 border-r border-border">
          <div className="p-3 border-b border-border">
            <h3 className="font-medium text-sm">File Explorer</h3>
          </div>
          <ScrollArea className="h-full">
            <div className="p-2">
              {fileTree.map(node => renderTreeNode(node))}
            </div>
          </ScrollArea>
        </div>

        {/* File Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {selectedFile ? (
            <>
              {/* File Header */}
              <div className="border-b border-border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getFileIcon(selectedFile.file_name, selectedFile.artifact_type)}
                    <div>
                      <h3 className="font-medium">{selectedFile.file_name}</h3>
                      <p className="text-sm text-muted-foreground">{selectedFile.file_path}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={getStatusColor(selectedFile.status)}>
                      {selectedFile.status.replace('_', ' ')}
                    </Badge>
                    <Badge variant="secondary">v{selectedFile.version}</Badge>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => copyToClipboard(selectedFile.content)}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                    <Dialog open={showFileViewer} onOpenChange={setShowFileViewer}>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Maximize2 className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-6xl max-h-[90vh]">
                        <DialogHeader>
                          <DialogTitle>{selectedFile.file_name}</DialogTitle>
                          <DialogDescription>{selectedFile.file_path}</DialogDescription>
                        </DialogHeader>
                        <ScrollArea className="h-[70vh]">
                          <pre className="text-sm bg-muted p-4 rounded-lg overflow-x-auto">
                            <code>{selectedFile.content}</code>
                          </pre>
                        </ScrollArea>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>

                {/* File metadata */}
                <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {selectedFile.agent_name}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(selectedFile.updated_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center gap-1">
                    <Code2 className="h-3 w-3" />
                    {selectedFile.content.split('\n').length} lines
                  </div>
                </div>

                {selectedFile.description && (
                  <p className="text-sm text-muted-foreground mt-2">{selectedFile.description}</p>
                )}
              </div>

              {/* File Content */}
              <Tabs defaultValue="content" className="flex-1 flex flex-col">
                <TabsList className="mx-4 mt-2 w-fit">
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="history">History</TabsTrigger>
                  <TabsTrigger value="metadata">Metadata</TabsTrigger>
                </TabsList>
                
                <TabsContent value="content" className="flex-1 m-0">
                  <ScrollArea className="h-full">
                    <pre className="text-sm p-4 overflow-x-auto">
                      <code>{selectedFile.content}</code>
                    </pre>
                  </ScrollArea>
                </TabsContent>
                
                <TabsContent value="history" className="flex-1 m-0 p-4">
                  <div className="text-center text-muted-foreground">
                    File history coming soon...
                  </div>
                </TabsContent>
                
                <TabsContent value="metadata" className="flex-1 m-0 p-4">
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Artifact ID:</span>
                        <p className="text-muted-foreground font-mono">{selectedFile.id}</p>
                      </div>
                      <div>
                        <span className="font-medium">Content Hash:</span>
                        <p className="text-muted-foreground font-mono">{selectedFile.content_hash.slice(0, 16)}...</p>
                      </div>
                      <div>
                        <span className="font-medium">Created:</span>
                        <p className="text-muted-foreground">{new Date(selectedFile.created_at).toLocaleString()}</p>
                      </div>
                      <div>
                        <span className="font-medium">Last Modified:</span>
                        <p className="text-muted-foreground">{new Date(selectedFile.updated_at).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <FileCode className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">Select a file to view</h3>
                <p className="text-muted-foreground">
                  Choose a file from the explorer to view its contents
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}