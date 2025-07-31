'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  X, 
  Plus, 
  Search, 
  Filter, 
  Clock, 
  AlertTriangle, 
  Users,
  Tag,
  Calendar,
  User
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
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
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useCommunicationStore } from '@/stores/communication-store'
import { Memo } from '@/types/communication'
import { formatRelativeTime, cn } from '@/lib/utils'

interface MemoPanelProps {
  isOpen: boolean
  onClose: () => void
}

const priorityColors = {
  low: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  medium: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  high: 'bg-red-500/10 text-red-500 border-red-500/20',
  urgent: 'bg-purple-500/10 text-purple-500 border-purple-500/20'
}

const priorityIcons = {
  low: Clock,
  medium: Clock,
  high: AlertTriangle,
  urgent: AlertTriangle
}

export function MemoPanel({ isOpen, onClose }: MemoPanelProps) {
  const { memos, users, currentUser, createMemo } = useCommunicationStore()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPriority, setSelectedPriority] = useState<string>('all')
  const [selectedTab, setSelectedTab] = useState('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  // Create memo form state
  const [newMemo, setNewMemo] = useState({
    title: '',
    content: '',
    recipients: [] as string[],
    priority: 'medium' as 'low' | 'medium' | 'high' | 'urgent',
    tags: ''
  })

  // Filter memos
  const filteredMemos = useMemo(() => {
    let filtered = memos

    // Filter by tab
    if (selectedTab === 'sent') {
      filtered = filtered.filter(m => m.createdBy === currentUser?.id)
    } else if (selectedTab === 'received') {
      filtered = filtered.filter(m => m.recipients.includes(currentUser?.id || ''))
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(m => 
        m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Filter by priority
    if (selectedPriority !== 'all') {
      filtered = filtered.filter(m => m.priority === selectedPriority)
    }

    return filtered.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  }, [memos, selectedTab, searchQuery, selectedPriority, currentUser?.id])

  const handleCreateMemo = async () => {
    if (!newMemo.title.trim() || !newMemo.content.trim() || newMemo.recipients.length === 0) {
      return
    }

    try {
      await createMemo(
        newMemo.title.trim(),
        newMemo.content.trim(),
        newMemo.recipients,
        newMemo.priority,
        newMemo.tags ? newMemo.tags.split(',').map(t => t.trim()).filter(Boolean) : undefined
      )

      // Reset form
      setNewMemo({
        title: '',
        content: '',
        recipients: [],
        priority: 'medium',
        tags: ''
      })
      setShowCreateDialog(false)
    } catch (error) {
      console.error('Failed to create memo:', error)
    }
  }

  const toggleRecipient = (userId: string) => {
    setNewMemo(prev => ({
      ...prev,
      recipients: prev.recipients.includes(userId)
        ? prev.recipients.filter(id => id !== userId)
        : [...prev.recipients, userId]
    }))
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-96 bg-background border-l border-border z-50 flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-sm">Memos & Announcements</h3>
          </div>
          <div className="flex items-center space-x-2">
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button size="sm" className="h-8 px-2">
                  <Plus className="h-4 w-4 mr-1" />
                  New
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create Memo</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title</Label>
                    <Input
                      id="title"
                      value={newMemo.title}
                      onChange={(e) => setNewMemo(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="Memo title..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="content">Content</Label>
                    <Textarea
                      id="content"
                      value={newMemo.content}
                      onChange={(e) => setNewMemo(prev => ({ ...prev, content: e.target.value }))}
                      placeholder="Write your memo..."
                      rows={4}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Recipients</Label>
                    <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
                      {users.filter(u => u.id !== currentUser?.id).map((user) => (
                        <div key={user.id} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={newMemo.recipients.includes(user.id)}
                            onChange={() => toggleRecipient(user.id)}
                            className="rounded"
                          />
                          <span className="text-sm">{user.name}</span>
                          <Badge variant="outline" className="text-xs">{user.role}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <Select 
                        value={newMemo.priority} 
                        onValueChange={(value: 'low' | 'medium' | 'high' | 'urgent') => 
                          setNewMemo(prev => ({ ...prev, priority: value }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="tags">Tags</Label>
                      <Input
                        id="tags"
                        value={newMemo.tags}
                        onChange={(e) => setNewMemo(prev => ({ ...prev, tags: e.target.value }))}
                        placeholder="tag1, tag2, tag3"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="outline"
                      onClick={() => setShowCreateDialog(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateMemo}
                      disabled={!newMemo.title.trim() || !newMemo.content.trim() || newMemo.recipients.length === 0}
                    >
                      Send Memo
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b border-border space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memos..."
              className="pl-9"
            />
          </div>

          <div className="flex space-x-2">
            <Select value={selectedPriority} onValueChange={setSelectedPriority}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3 mx-4 mt-2">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="received">Received</TabsTrigger>
            <TabsTrigger value="sent">Sent</TabsTrigger>
          </TabsList>

          <TabsContent value={selectedTab} className="flex-1 mt-0">
            <ScrollArea className="h-full">
              <div className="p-4 space-y-3">
                {filteredMemos.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-muted-foreground text-sm">No memos found</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {selectedTab === 'sent' ? 'Create your first memo!' : 'No memos to display'}
                    </div>
                  </div>
                ) : (
                  filteredMemos.map((memo) => {
                    const creator = users.find(u => u.id === memo.createdBy)
                    const PriorityIcon = priorityIcons[memo.priority]

                    return (
                      <Card key={memo.id} className="hover:bg-muted/30 transition-colors">
                        <CardHeader className="pb-2">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-sm truncate">{memo.title}</h4>
                              <div className="flex items-center space-x-2 mt-1">
                                <div className="flex items-center text-xs text-muted-foreground">
                                  <User className="h-3 w-3 mr-1" />
                                  {creator?.name}
                                </div>
                                <div className="flex items-center text-xs text-muted-foreground">
                                  <Calendar className="h-3 w-3 mr-1" />
                                  {formatRelativeTime(memo.createdAt)}
                                </div>
                              </div>
                            </div>
                            <Badge 
                              className={cn("text-xs border", priorityColors[memo.priority])}
                              variant="outline"
                            >
                              <PriorityIcon className="h-3 w-3 mr-1" />
                              {memo.priority}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
                            {memo.content}
                          </p>
                          
                          <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center space-x-3">
                              <div className="flex items-center text-muted-foreground">
                                <Users className="h-3 w-3 mr-1" />
                                {memo.recipients.length} recipients
                              </div>
                              {memo.tags.length > 0 && (
                                <div className="flex items-center space-x-1">
                                  <Tag className="h-3 w-3 text-muted-foreground" />
                                  {memo.tags.slice(0, 2).map((tag) => (
                                    <Badge key={tag} variant="secondary" className="text-xs px-1 py-0">
                                      {tag}
                                    </Badge>
                                  ))}
                                  {memo.tags.length > 2 && (
                                    <span className="text-muted-foreground">+{memo.tags.length - 2}</span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )
                  })
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </motion.div>
    </AnimatePresence>
  )
}