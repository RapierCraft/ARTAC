'use client'

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Upload, 
  File, 
  Image, 
  Video, 
  Music, 
  Archive, 
  FileText,
  Download,
  Trash2,
  Eye,
  Share2,
  MoreVertical,
  X,
  Progress,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress as ProgressBar } from '@/components/ui/progress'
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
  DialogTitle
} from '@/components/ui/dialog'
import { useCommunicationStore } from '@/stores/communication-store'
import { FileUpload } from '@/types/communication'
import { formatBytes, formatRelativeTime, cn } from '@/lib/utils'

interface FileSharingProps {
  channelId: string
  onFileSelect?: (file: FileUpload) => void
}

interface UploadProgress {
  id: string
  name: string
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

// Mock file data
const mockFiles: FileUpload[] = [
  {
    id: 'file-1',
    name: 'ARTAC_Architecture_Design.pdf',
    type: 'application/pdf',
    size: 2457600, // 2.4 MB
    uploadedBy: 'user-2',
    uploadedAt: new Date('2024-11-25T14:30:00'),
    channelId: 'channel-dev',
    url: '/api/files/ARTAC_Architecture_Design.pdf',
    isPublic: true,
    downloadCount: 12
  },
  {
    id: 'file-2',
    name: 'demo_video.mp4',
    type: 'video/mp4',
    size: 15728640, // 15 MB
    uploadedBy: 'user-1',
    uploadedAt: new Date('2024-11-24T16:45:00'),
    channelId: 'channel-general',
    url: '/api/files/demo_video.mp4',
    thumbnailUrl: '/api/files/demo_video_thumb.jpg',
    isPublic: true,
    downloadCount: 34
  },
  {
    id: 'file-3',
    name: 'meeting_notes.docx',
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    size: 524288, // 512 KB
    uploadedBy: 'user-3',
    uploadedAt: new Date('2024-11-23T11:20:00'),
    channelId: 'channel-exec',
    url: '/api/files/meeting_notes.docx',
    isPublic: false,
    downloadCount: 8
  },
  {
    id: 'file-4',
    name: 'ui_mockups.zip',
    type: 'application/zip',
    size: 8388608, // 8 MB
    uploadedBy: 'user-5',
    uploadedAt: new Date('2024-11-22T09:15:00'),
    channelId: 'channel-design',
    url: '/api/files/ui_mockups.zip',
    isPublic: true,
    downloadCount: 23
  },
  {
    id: 'file-5',
    name: 'team_photo.jpg',
    type: 'image/jpeg',
    size: 1048576, // 1 MB
    uploadedBy: 'user-1',
    uploadedAt: new Date('2024-11-21T15:30:00'),
    channelId: 'channel-general',
    url: '/api/files/team_photo.jpg',
    thumbnailUrl: '/api/files/team_photo_thumb.jpg',
    isPublic: true,
    downloadCount: 45
  }
]

export function FileSharing({ channelId, onFileSelect }: FileSharingProps) {
  const { users, currentUser } = useCommunicationStore()
  
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploads, setUploads] = useState<UploadProgress[]>([])
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const channelFiles = mockFiles.filter(f => f.channelId === channelId)

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return Image
    if (type.startsWith('video/')) return Video
    if (type.startsWith('audio/')) return Music
    if (type.includes('pdf')) return FileText
    if (type.includes('zip') || type.includes('rar')) return Archive
    return File
  }

  const getFileColor = (type: string) => {
    if (type.startsWith('image/')) return 'text-green-500'
    if (type.startsWith('video/')) return 'text-blue-500'
    if (type.startsWith('audio/')) return 'text-purple-500'
    if (type.includes('pdf')) return 'text-red-500'
    if (type.includes('zip') || type.includes('rar')) return 'text-yellow-500'
    return 'text-gray-500'
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = Array.from(e.dataTransfer.files)
    handleFileUpload(files)
  }, [])

  const handleFileUpload = async (files: File[]) => {
    for (const file of files) {
      const uploadId = `upload-${Date.now()}-${Math.random()}`
      
      // Add to upload progress
      setUploads(prev => [...prev, {
        id: uploadId,
        name: file.name,
        progress: 0,
        status: 'uploading'
      }])

      try {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploads(prev => prev.map(upload => {
            if (upload.id === uploadId && upload.progress < 95) {
              return { ...upload, progress: upload.progress + Math.random() * 20 }
            }
            return upload
          }))
        }, 200)

        // Simulate upload completion after 3 seconds
        setTimeout(() => {
          clearInterval(progressInterval)
          setUploads(prev => prev.map(upload => {
            if (upload.id === uploadId) {
              return { ...upload, progress: 100, status: 'completed' }
            }
            return upload
          }))

          // Remove from uploads after 2 seconds
          setTimeout(() => {
            setUploads(prev => prev.filter(upload => upload.id !== uploadId))
          }, 2000)
        }, 3000)

        console.log('Uploading file:', file.name, file.size, file.type)
        
      } catch (error) {
        console.error('Upload failed:', error)
        setUploads(prev => prev.map(upload => {
          if (upload.id === uploadId) {
            return { 
              ...upload, 
              status: 'error', 
              error: 'Upload failed. Please try again.' 
            }
          }
          return upload
        }))
      }
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) {
      handleFileUpload(files)
    }
  }

  const handleDownload = (file: FileUpload) => {
    // In real implementation, this would trigger download
    console.log('Downloading file:', file.name)
  }

  const handleShare = (file: FileUpload) => {
    // In real implementation, this would copy share link
    navigator.clipboard.writeText(`${window.location.origin}${file.url}`)
    console.log('Share link copied for:', file.name)
  }

  const handleDelete = (file: FileUpload) => {
    // In real implementation, this would delete the file
    console.log('Deleting file:', file.id)
  }

  const canPreview = (file: FileUpload) => {
    return file.type.startsWith('image/') || 
           file.type.startsWith('video/') || 
           file.type === 'application/pdf'
  }

  return (
    <div className="h-full flex flex-col">
      {/* Upload Area */}
      <div
        className={cn(
          "p-6 border-2 border-dashed rounded-lg transition-colors m-4",
          isDragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
          <p className="text-sm font-medium mb-1">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground mb-3">
            Supports images, videos, documents, and archives up to 50MB
          </p>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => fileInputRef.current?.click()}
          >
            Browse Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileInputChange}
            accept="image/*,video/*,audio/*,.pdf,.doc,.docx,.txt,.zip,.rar"
          />
        </div>
      </div>

      {/* Upload Progress */}
      <AnimatePresence>
        {uploads.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mx-4 mb-4 space-y-2"
          >
            {uploads.map((upload) => (
              <Card key={upload.id} className="p-3">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    {upload.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : upload.status === 'error' ? (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    ) : (
                      <Upload className="h-5 w-5 text-blue-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{upload.name}</div>
                    {upload.status === 'uploading' && (
                      <ProgressBar value={upload.progress} className="mt-2" />
                    )}
                    {upload.status === 'error' && (
                      <div className="text-xs text-red-500 mt-1">{upload.error}</div>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {upload.status === 'uploading' && `${Math.round(upload.progress)}%`}
                    {upload.status === 'completed' && 'Done'}
                    {upload.status === 'error' && 'Failed'}
                  </div>
                </div>
              </Card>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Files List */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 space-y-3">
            {channelFiles.length === 0 ? (
              <div className="text-center py-8">
                <File className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
                <div className="text-sm text-muted-foreground">No files shared yet</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Upload files to share with your team
                </div>
              </div>
            ) : (
              channelFiles.map((file) => {
                const uploader = users.find(u => u.id === file.uploadedBy)
                const FileIcon = getFileIcon(file.type)
                const fileColor = getFileColor(file.type)

                return (
                  <Card 
                    key={file.id} 
                    className="hover:bg-muted/30 transition-colors cursor-pointer"
                    onClick={() => onFileSelect?.(file)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-3">
                        {/* File Icon/Thumbnail */}
                        <div className="flex-shrink-0">
                          {file.thumbnailUrl ? (
                            <img
                              src={file.thumbnailUrl}
                              alt={file.name}
                              className="h-12 w-12 rounded object-cover"
                            />
                          ) : (
                            <div className="h-12 w-12 rounded bg-muted flex items-center justify-center">
                              <FileIcon className={cn("h-6 w-6", fileColor)} />
                            </div>
                          )}
                        </div>

                        {/* File Info */}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm truncate">{file.name}</div>
                          <div className="flex items-center space-x-3 text-xs text-muted-foreground mt-1">
                            <span>{formatBytes(file.size)}</span>
                            <span>by {uploader?.name}</span>
                            <span>{formatRelativeTime(file.uploadedAt)}</span>
                            <span>{file.downloadCount} downloads</span>
                          </div>
                          {!file.isPublic && (
                            <Badge variant="secondary" className="text-xs mt-1">
                              Private
                            </Badge>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center space-x-1">
                          {canPreview(file) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                setSelectedFile(file)
                                setShowPreview(true)
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          )}
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDownload(file)
                            }}
                          >
                            <Download className="h-4 w-4" />
                          </Button>

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
                              <DropdownMenuItem onClick={() => handleShare(file)}>
                                <Share2 className="h-4 w-4 mr-2" />
                                Copy Link
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              {(file.uploadedBy === currentUser?.id || currentUser?.role === 'CEO') && (
                                <DropdownMenuItem 
                                  className="text-destructive"
                                  onClick={() => handleDelete(file)}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </ScrollArea>
      </div>

      {/* File Preview Dialog */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle>{selectedFile?.name}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex items-center justify-center p-4">
            {selectedFile?.type.startsWith('image/') && (
              <img
                src={selectedFile.url}
                alt={selectedFile.name}
                className="max-w-full max-h-full object-contain"
              />
            )}
            {selectedFile?.type.startsWith('video/') && (
              <video
                src={selectedFile.url}
                controls
                className="max-w-full max-h-full"
              />
            )}
            {selectedFile?.type === 'application/pdf' && (
              <iframe
                src={selectedFile.url}
                className="w-full h-full border-0"
                title={selectedFile.name}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}