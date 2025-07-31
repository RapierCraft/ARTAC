'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Mic, 
  MicOff, 
  Headphones, 
  HeadphonesOff, 
  PhoneOff, 
  Settings, 
  Volume2,
  VolumeX,
  Monitor,
  Video,
  VideoOff,
  Users,
  Phone
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useCommunicationStore } from '@/stores/communication-store'
import { cn } from '@/lib/utils'

interface VoiceChannelProps {
  channelId: string
  isMinimized?: boolean
  onMinimize?: () => void
}

export function VoiceChannel({ channelId, isMinimized = false, onMinimize }: VoiceChannelProps) {
  const { channels, users, currentUser } = useCommunicationStore()
  
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isDeafened, setIsDeafened] = useState(false)
  const [isVideoEnabled, setIsVideoEnabled] = useState(false)
  const [isScreenSharing, setIsScreenSharing] = useState(false)
  const [volume, setVolume] = useState([100])
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [selectedMicrophone, setSelectedMicrophone] = useState<string>('')
  const [selectedSpeaker, setSelectedSpeaker] = useState<string>('')
  
  // WebRTC refs
  const localStreamRef = useRef<MediaStream | null>(null)
  const peerConnectionsRef = useRef<Map<string, RTCPeerConnection>>(new Map())
  const localVideoRef = useRef<HTMLVideoElement>(null)

  const channel = channels.find(c => c.id === channelId)
  const connectedUsers = channel?.connectedUsers || []
  const connectedUsersData = users.filter(u => connectedUsers.includes(u.id))

  // Initialize media devices
  useEffect(() => {
    const getDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        setAudioDevices(devices.filter(d => d.kind === 'audioinput' || d.kind === 'audiooutput'))
      } catch (error) {
        console.error('Failed to get media devices:', error)
      }
    }
    getDevices()
  }, [])

  // Handle voice connection
  const handleConnect = async () => {
    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      localStreamRef.current = stream
      setIsConnected(true)
      
      // In a real implementation, this would establish WebRTC connections
      // with other users in the channel
      console.log('Connected to voice channel:', channelId)
      
    } catch (error) {
      console.error('Failed to connect to voice channel:', error)
    }
  }

  const handleDisconnect = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop())
      localStreamRef.current = null
    }
    
    // Close all peer connections
    peerConnectionsRef.current.forEach(pc => pc.close())
    peerConnectionsRef.current.clear()
    
    setIsConnected(false)
    setIsVideoEnabled(false)
    setIsScreenSharing(false)
  }

  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0]
      if (audioTrack) {
        audioTrack.enabled = isMuted
        setIsMuted(!isMuted)
      }
    }
  }

  const toggleDeafen = () => {
    setIsDeafened(!isDeafened)
    // In real implementation, this would mute/unmute all incoming audio
  }

  const toggleVideo = async () => {
    if (!isVideoEnabled) {
      try {
        const videoStream = await navigator.mediaDevices.getUserMedia({ video: true })
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = videoStream
        }
        setIsVideoEnabled(true)
      } catch (error) {
        console.error('Failed to enable video:', error)
      }
    } else {
      if (localVideoRef.current?.srcObject) {
        const stream = localVideoRef.current.srcObject as MediaStream
        stream.getVideoTracks().forEach(track => track.stop())
        localVideoRef.current.srcObject = null
      }
      setIsVideoEnabled(false)
    }
  }

  const startScreenShare = async () => {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({ 
        video: true, 
        audio: true 
      })
      setIsScreenSharing(true)
      
      // Handle screen share end
      screenStream.getVideoTracks()[0].onended = () => {
        setIsScreenSharing(false)
      }
    } catch (error) {
      console.error('Failed to start screen share:', error)
    }
  }

  if (isMinimized) {
    return (
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="fixed bottom-4 right-4 z-50"
      >
        <Card className="p-3 bg-card/95 backdrop-blur-sm border-green-500/50">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs font-medium">Voice Connected</span>
            </div>
            <div className="flex items-center space-x-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={toggleMute}
              >
                {isMuted ? <MicOff className="h-3 w-3" /> : <Mic className="h-3 w-3" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 text-red-500"
                onClick={handleDisconnect}
              >
                <PhoneOff className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={onMinimize}
              >
                <Users className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </Card>
      </motion.div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-card">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-green-500 rounded-full" />
            <h3 className="font-semibold text-sm">{channel?.name}</h3>
            <Badge variant="secondary" className="text-xs">
              {connectedUsers.length} connected
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onMinimize}
            className="h-8 w-8 p-0"
          >
            <Users className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Connected Users */}
      <div className="flex-1 p-4 space-y-3 overflow-y-auto">
        {connectedUsersData.map((user) => (
          <div key={user.id} className="flex items-center space-x-3 p-2 rounded-lg bg-muted/30">
            <div className="relative">
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-sm font-medium">
                {user.avatar || user.name.charAt(0)}
              </div>
              {user.isSpeaking && (
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="absolute -inset-1 rounded-full border-2 border-green-500"
                />
              )}
              {user.isMuted && (
                <div className="absolute -bottom-1 -right-1 h-4 w-4 bg-red-500 rounded-full flex items-center justify-center">
                  <MicOff className="h-2 w-2 text-white" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium">{user.name}</div>
              <div className="text-xs text-muted-foreground">{user.role}</div>
            </div>
            {user.isInVoiceChannel && (
              <div className="flex items-center space-x-1">
                <Volume2 className="h-3 w-3 text-green-500" />
              </div>
            )}
          </div>
        ))}

        {/* Local Video Preview */}
        <AnimatePresence>
          {isVideoEnabled && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="relative rounded-lg overflow-hidden bg-black"
            >
              <video
                ref={localVideoRef}
                autoPlay
                muted
                className="w-full aspect-video object-cover"
              />
              <div className="absolute bottom-2 left-2 text-xs text-white bg-black/50 px-2 py-1 rounded">
                You
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Controls */}
      <div className="p-4 border-t border-border">
        {isConnected ? (
          <div className="space-y-4">
            {/* Volume Control */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Volume</span>
                <span className="text-xs text-muted-foreground">{volume[0]}%</span>
              </div>
              <Slider
                value={volume}
                onValueChange={setVolume}
                max={100}
                step={1}
                className="w-full"
              />
            </div>

            {/* Main Controls */}
            <div className="flex items-center space-x-2">
              <Button
                variant={isMuted ? "destructive" : "secondary"}
                size="sm"
                onClick={toggleMute}
                className="flex-1"
              >
                {isMuted ? <MicOff className="h-4 w-4 mr-2" /> : <Mic className="h-4 w-4 mr-2" />}
                {isMuted ? 'Unmute' : 'Mute'}
              </Button>
              
              <Button
                variant={isDeafened ? "destructive" : "secondary"}
                size="sm"
                onClick={toggleDeafen}
                className="flex-1"
              >
                {isDeafened ? <HeadphonesOff className="h-4 w-4 mr-2" /> : <Headphones className="h-4 w-4 mr-2" />}
                {isDeafened ? 'Undeafen' : 'Deafen'}
              </Button>
            </div>

            {/* Additional Controls */}
            <div className="flex items-center space-x-2">
              <Button
                variant={isVideoEnabled ? "default" : "outline"}
                size="sm"
                onClick={toggleVideo}
                className="flex-1"
              >
                {isVideoEnabled ? <Video className="h-4 w-4 mr-2" /> : <VideoOff className="h-4 w-4 mr-2" />}
                Video
              </Button>
              
              <Button
                variant={isScreenSharing ? "default" : "outline"}
                size="sm"
                onClick={startScreenShare}
                className="flex-1"
              >
                <Monitor className="h-4 w-4 mr-2" />
                Screen
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>
                    Audio Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    Video Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    Noise Reduction: On
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    Echo Cancellation: On
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Disconnect */}
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDisconnect}
              className="w-full"
            >
              <PhoneOff className="h-4 w-4 mr-2" />
              Disconnect
            </Button>
          </div>
        ) : (
          <Button
            onClick={handleConnect}
            className="w-full"
            size="lg"
          >
            <Phone className="h-4 w-4 mr-2" />
            Join Voice Channel
          </Button>
        )}
      </div>
    </div>
  )
}