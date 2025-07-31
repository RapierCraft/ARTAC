'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Plus, 
  Search, 
  Filter, 
  ChevronUp, 
  ChevronDown, 
  Pin, 
  Lock, 
  MessageSquare, 
  Eye,
  Calendar,
  User,
  Tag,
  ThumbsUp,
  ThumbsDown,
  MoreVertical,
  Edit,
  Trash2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { useCommunicationStore } from '@/stores/communication-store'
import { ForumPost, ForumCategory } from '@/types/communication'
import { formatRelativeTime, cn } from '@/lib/utils'

interface ForumChannelProps {
  channelId: string
}

const mockCategories: ForumCategory[] = [
  { id: 'general', name: 'General Discussion', color: 'blue', description: 'General company topics', moderators: [] },
  { id: 'announcements', name: 'Announcements', color: 'red', description: 'Important company announcements', moderators: ['user-1'] },
  { id: 'projects', name: 'Project Updates', color: 'green', description: 'Project status and updates', moderators: ['user-2', 'user-3'] },
  { id: 'feedback', name: 'Feedback', color: 'purple', description: 'Company feedback and suggestions', moderators: [] },
  { id: 'resources', name: 'Resources', color: 'orange', description: 'Helpful resources and guides', moderators: ['user-4'] }
]

const mockPosts: ForumPost[] = [
  {
    id: 'post-1',
    channelId: 'forum-general',
    categoryId: 'announcements',
    title: 'Q4 Company All-Hands Meeting Scheduled',
    content: 'We\'re pleased to announce our Q4 All-Hands meeting will be held on December 15th. This will cover our yearly achievements, upcoming projects, and team recognition.',
    author: 'user-1',
    createdAt: new Date('2024-11-01'),
    isPinned: true,
    isLocked: false,
    upvotes: ['user-2', 'user-3', 'user-4', 'user-5'],
    downvotes: [],
    replies: [],
    tags: ['meeting', 'q4', 'all-hands'],
    attachments: [],
    views: 127
  },
  {
    id: 'post-2',
    channelId: 'forum-general',
    categoryId: 'projects',
    title: 'ARTAC Mission Control Dashboard - Development Update',
    content: 'Great progress on the Mission Control dashboard! We\'ve successfully implemented the communication webapp with advanced features including voice channels, forums, and real-time messaging. Next phase will focus on analytics and performance monitoring.',
    author: 'user-2',
    createdAt: new Date('2024-11-25'),
    isPinned: false,
    isLocked: false,
    upvotes: ['user-1', 'user-3', 'user-5'],
    downvotes: [],
    replies: [],
    tags: ['artac', 'development', 'dashboard'],
    attachments: [],
    views: 89
  },
  {
    id: 'post-3',
    channelId: 'forum-general',
    categoryId: 'feedback',
    title: 'Suggestion: Team Recognition Program',
    content: 'I think we should implement a peer-to-peer recognition program where team members can nominate each other for excellent work. This could help boost morale and highlight great contributions that might otherwise go unnoticed.',
    author: 'user-5',
    createdAt: new Date('2024-11-20'),
    isPinned: false,
    isLocked: false,
    upvotes: ['user-1', 'user-2', 'user-4'],
    downvotes: ['user-3'],
    replies: [],
    tags: ['hr', 'recognition', 'team'],
    attachments: [],
    views: 76
  }
]

export function ForumChannel({ channelId }: ForumChannelProps) {
  const { users, currentUser } = useCommunicationStore()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'popular' | 'replies'>('newest')
  const [showCreatePost, setShowCreatePost] = useState(false)
  const [selectedPost, setSelectedPost] = useState<ForumPost | null>(null)

  // Create post form state
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    categoryId: '',
    tags: ''
  })

  // Filter and sort posts
  const filteredPosts = useMemo(() => {
    let filtered = mockPosts

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(post => 
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(post => post.categoryId === selectedCategory)
    }

    // Sort posts
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        case 'oldest':
          return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        case 'popular':
          return (b.upvotes.length - b.downvotes.length) - (a.upvotes.length - a.downvotes.length)
        case 'replies':
          return b.replies.length - a.replies.length
        default:
          return 0
      }
    })
  }, [searchQuery, selectedCategory, sortBy])

  const handleCreatePost = () => {
    if (!newPost.title.trim() || !newPost.content.trim() || !newPost.categoryId) return

    // In real implementation, this would create the post
    console.log('Creating forum post:', newPost)
    
    // Reset form
    setNewPost({ title: '', content: '', categoryId: '', tags: '' })
    setShowCreatePost(false)
  }

  const handleVote = (postId: string, type: 'up' | 'down') => {
    // In real implementation, this would update the vote
    console.log('Voting on post:', postId, type)
  }

  const getCategoryColor = (categoryId: string) => {
    const category = mockCategories.find(c => c.id === categoryId)
    return category?.color || 'gray'
  }

  const getCategoryName = (categoryId: string) => {
    const category = mockCategories.find(c => c.id === categoryId)
    return category?.name || 'Unknown'
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">Company Forum</h2>
            <p className="text-sm text-muted-foreground">
              Discuss projects, share ideas, and stay informed
            </p>
          </div>
          <Dialog open={showCreatePost} onOpenChange={setShowCreatePost}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Post
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Create New Forum Post</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    value={newPost.title}
                    onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="What's your post about?"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select 
                    value={newPost.categoryId} 
                    onValueChange={(value) => setNewPost(prev => ({ ...prev, categoryId: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockCategories.map((category) => (
                        <SelectItem key={category.id} value={category.id}>
                          <div className="flex items-center space-x-2">
                            <div className={`h-2 w-2 rounded-full bg-${category.color}-500`} />
                            <span>{category.name}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="content">Content</Label>
                  <Textarea
                    id="content"
                    value={newPost.content}
                    onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Share your thoughts, ideas, or questions..."
                    rows={6}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tags">Tags (optional)</Label>
                  <Input
                    id="tags"
                    value={newPost.tags}
                    onChange={(e) => setNewPost(prev => ({ ...prev, tags: e.target.value }))}
                    placeholder="tag1, tag2, tag3"
                  />
                </div>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowCreatePost(false)}>
                    Cancel
                  </Button>
                  <Button 
                    onClick={handleCreatePost}
                    disabled={!newPost.title.trim() || !newPost.content.trim() || !newPost.categoryId}
                  >
                    Create Post
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search posts..."
                className="pl-9"
              />
            </div>
          </div>
          
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {mockCategories.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  <div className="flex items-center space-x-2">
                    <div className={`h-2 w-2 rounded-full bg-${category.color}-500`} />
                    <span>{category.name}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest</SelectItem>
              <SelectItem value="oldest">Oldest</SelectItem>
              <SelectItem value="popular">Popular</SelectItem>
              <SelectItem value="replies">Most Replies</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Posts List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {filteredPosts.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-muted-foreground text-sm">No posts found</div>
              <div className="text-xs text-muted-foreground mt-1">
                {searchQuery ? 'Try adjusting your search terms' : 'Be the first to create a post!'}
              </div>
            </div>
          ) : (
            filteredPosts.map((post) => {
              const author = users.find(u => u.id === post.author)
              const categoryColor = getCategoryColor(post.categoryId!)

              return (
                <Card 
                  key={post.id} 
                  className={cn(
                    "hover:bg-muted/30 transition-colors cursor-pointer",
                    post.isPinned && "border-yellow-500/50 bg-yellow-500/5"
                  )}
                  onClick={() => setSelectedPost(post)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center space-x-2">
                          {post.isPinned && (
                            <Pin className="h-4 w-4 text-yellow-500" />
                          )}
                          {post.isLocked && (
                            <Lock className="h-4 w-4 text-red-500" />
                          )}
                          <Badge 
                            variant="secondary" 
                            className={`bg-${categoryColor}-500/10 text-${categoryColor}-500 border-${categoryColor}-500/20`}
                          >
                            {getCategoryName(post.categoryId!)}
                          </Badge>
                        </div>
                        
                        <h3 className="font-semibold text-lg leading-tight">
                          {post.title}
                        </h3>
                        
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {post.content}
                        </p>

                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <div className="flex items-center space-x-1">
                            <User className="h-3 w-3" />
                            <span>{author?.name}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatRelativeTime(post.createdAt)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Eye className="h-3 w-3" />
                            <span>{post.views} views</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <MessageSquare className="h-3 w-3" />
                            <span>{post.replies.length} replies</span>
                          </div>
                        </div>

                        {post.tags.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <Tag className="h-3 w-3 text-muted-foreground" />
                            <div className="flex flex-wrap gap-1">
                              {post.tags.map((tag) => (
                                <Badge key={tag} variant="outline" className="text-xs px-1 py-0">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col items-center space-y-2 ml-4">
                        <div className="flex items-center space-x-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleVote(post.id, 'up')
                            }}
                          >
                            <ChevronUp className="h-4 w-4" />
                          </Button>
                          <span className="text-sm font-medium">
                            {post.upvotes.length - post.downvotes.length}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleVote(post.id, 'down')
                            }}
                          >
                            <ChevronDown className="h-4 w-4" />
                          </Button>
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {post.author === currentUser?.id && (
                              <>
                                <DropdownMenuItem>
                                  <Edit className="h-4 w-4 mr-2" />
                                  Edit Post
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-destructive">
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete Post
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                              </>
                            )}
                            <DropdownMenuItem>
                              <Pin className="h-4 w-4 mr-2" />
                              {post.isPinned ? 'Unpin' : 'Pin'} Post
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Lock className="h-4 w-4 mr-2" />
                              {post.isLocked ? 'Unlock' : 'Lock'} Post
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardHeader>
                </Card>
              )
            })
          )}
        </div>
      </ScrollArea>
    </div>
  )
}