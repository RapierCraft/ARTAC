'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Volume2, VolumeX, Users, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface VoiceInterfaceProps {
  isActive: boolean
  onToggle: () => void
}

type ConversationMode = 'ceo' | 'team-meeting' | 'task-assignment'

export function VoiceInterface({ isActive, onToggle }: VoiceInterfaceProps) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [conversationMode, setConversationMode] = useState<ConversationMode>('ceo')
  const [lastResponse, setLastResponse] = useState<string>('')
  const [audioUrl, setAudioUrl] = useState<string>('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [whisperAvailable, setWhisperAvailable] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioStreamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  // Initialize Whisper STT and check availability
  useEffect(() => {
    const checkWhisperAvailability = async () => {
      try {
        console.log('Checking Whisper STT availability...')
        const response = await fetch('http://localhost:8000/api/v1/voice/whisper/status')
        const status = await response.json()
        
        if (status.whisper_service_initialized) {
          setWhisperAvailable(true)
          console.log('Whisper STT available:', status)
        } else {
          setWhisperAvailable(false)
          console.log('Whisper STT not available:', status)
        }
      } catch (error) {
        console.error('Failed to check Whisper availability:', error)
        setWhisperAvailable(false)
      }
    }
    
    checkWhisperAvailability()
  }, [])

  // Start/stop audio recording
  useEffect(() => {
    if (isActive && whisperAvailable) {
      startRecording()
    } else {
      stopRecording()
    }
  }, [isActive, whisperAvailable])
  
  // Start audio recording
  const startRecording = async () => {
    try {
      console.log('Starting audio recording for Whisper STT...')
      setLastResponse('🎤 Starting recording... Speak now!')
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      })
      
      audioStreamRef.current = stream
      audioChunksRef.current = []
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        console.log('Recording stopped, processing audio...')
        setIsListening(false)
        setIsProcessing(true)
        
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await processAudioWithWhisper(audioBlob)
      }
      
      mediaRecorder.start(1000) // Collect data every second
      setIsListening(true)
      
    } catch (error) {
      console.error('Failed to start recording:', error)
      setLastResponse('❌ Failed to access microphone. Please allow microphone permissions.')
      setIsListening(false)
    }
  }
  
  // Stop audio recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('Stopping audio recording...')
      mediaRecorderRef.current.stop()
    }
    
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
      audioStreamRef.current = null
    }
    
    setIsListening(false)
  }

  // Process audio with Whisper STT
  const processAudioWithWhisper = async (audioBlob: Blob) => {
    try {
      console.log('Processing audio with Whisper STT...')
      setLastResponse('🧠 Processing speech...')
      
      const formData = new FormData()
      formData.append('audio_file', audioBlob, 'recording.webm')
      formData.append('conversation_mode', conversationMode)
      formData.append('language', 'en')
      
      const response = await fetch('http://localhost:8000/api/v1/voice/whisper/transcribe-and-respond', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const result = await response.json()
        console.log('Whisper STT + Response result:', result)
        
        // Display transcription
        setTranscript(result.transcription.text)
        
        // Display AI response
        if (result.response) {
          setLastResponse(result.response.response_text)
          
          // Set up audio playback if available
          if (result.response.audio_file) {
            const audioFileName = result.response.audio_file.split('/').pop()
            setAudioUrl(`http://localhost:8000/api/v1/voice/voice/download-audio/${audioFileName}`)
          }
        }
        
      } else {
        const error = await response.json()
        console.error('Whisper processing failed:', error)
        setLastResponse(`❌ Processing failed: ${error.detail || 'Unknown error'}`)
      }
      
    } catch (error) {
      console.error('Failed to process audio with Whisper:', error)
      setLastResponse('❌ Failed to process audio. Please try again.')
    } finally {
      setIsProcessing(false)
      setTranscript('')
    }
  }
  
  // Test microphone and Whisper service
  const testMicrophoneAndWhisper = async () => {
    try {
      console.log('Testing microphone and Whisper service...')
      setLastResponse('🔍 Testing microphone and Whisper service...')
      
      // Test microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      
      // Test Whisper service
      const whisperResponse = await fetch('http://localhost:8000/api/v1/voice/whisper/test-transcription', {
        method: 'POST'
      })
      
      if (whisperResponse.ok) {
        const result = await whisperResponse.json()
        console.log('Whisper test result:', result)
        
        setLastResponse(`✅ All systems ready! 
🎤 Microphone: Accessible
🧠 Whisper STT: ${result.whisper_available ? 'Available' : 'Not available'}
🎧 ElevenLabs TTS: Ready

Click the voice button to start recording!`)
      } else {
        setLastResponse('⚠️ Microphone OK, but Whisper service test failed')
      }
      
    } catch (error) {
      console.error('Test failed:', error)
      setLastResponse('❌ Test failed. Please check microphone permissions and backend connection.')
    }
  }

  // Legacy function - now handled by processAudioWithWhisper
  // Keeping for backward compatibility
  const processVoiceCommand = async (command: string) => {
    console.log('Legacy processVoiceCommand called with:', command)
    // This is now handled by the Whisper STT pipeline
  }

  // Helper functions to extract information from voice commands
  const extractTaskTitle = (command: string): string => {
    const taskWords = ['build', 'create', 'develop', 'implement', 'design']
    const words = command.toLowerCase().split(' ')
    const taskIndex = words.findIndex(word => taskWords.includes(word))
    return taskIndex !== -1 ? words.slice(taskIndex).join(' ') : 'Voice Task'
  }

  const extractSkills = (command: string): string[] => {
    const skillKeywords = {
      'backend': ['backend', 'server', 'api', 'database'],
      'frontend': ['frontend', 'ui', 'interface', 'web'],
      'security': ['security', 'auth', 'authentication', 'secure'],
      'devops': ['deploy', 'infrastructure', 'docker', 'cloud'],
      'database': ['database', 'sql', 'data']
    }
    
    const skills: string[] = []
    const lowerCommand = command.toLowerCase()
    
    Object.entries(skillKeywords).forEach(([skill, keywords]) => {
      if (keywords.some(keyword => lowerCommand.includes(keyword))) {
        skills.push(skill)
      }
    })
    
    return skills.length > 0 ? skills : ['general']
  }

  const extractPriority = (command: string): string => {
    const lowerCommand = command.toLowerCase()
    if (lowerCommand.includes('urgent') || lowerCommand.includes('critical')) return 'high'
    if (lowerCommand.includes('low priority') || lowerCommand.includes('when you can')) return 'low'
    return 'medium'
  }

  const extractEstimatedHours = (command: string): number => {
    const hourMatch = command.match(/(\d+)\s*hours?/i)
    const dayMatch = command.match(/(\d+)\s*days?/i)
    
    if (hourMatch) return parseInt(hourMatch[1])
    if (dayMatch) return parseInt(dayMatch[1]) * 8
    return 8 // Default to 8 hours
  }

  // Play audio response
  const playAudioResponse = () => {
    if (audioUrl && audioRef.current) {
      setIsPlaying(true)
      audioRef.current.src = audioUrl
      audioRef.current.play()
    }
  }

  // Generate audio level visualization
  useEffect(() => {
    if (isListening) {
      const interval = setInterval(() => {
        setAudioLevel(Math.random() * 100)
      }, 100)
      return () => clearInterval(interval)
    } else {
      setAudioLevel(0)
    }
  }, [isListening])

  // Handle audio events
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.onended = () => setIsPlaying(false)
      audioRef.current.onerror = () => setIsPlaying(false)
    }
  }, [])

  return (
    <div className="flex flex-col items-center space-y-4 relative z-30">
      {/* Conversation Mode Selector */}
      <div className="w-full max-w-xs relative z-40">
        <Select value={conversationMode} onValueChange={(value: ConversationMode) => setConversationMode(value)}>
          <SelectTrigger className="w-full bg-background border-slate-700">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ceo">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>Talk to CEO</span>
              </div>
            </SelectItem>
            <SelectItem value="team-meeting">
              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4" />
                <span>Team Meeting</span>
              </div>
            </SelectItem>
            <SelectItem value="task-assignment">
              <div className="flex items-center space-x-2">
                <Mic className="h-4 w-4" />
                <span>Assign Task</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Main Voice Button */}
      <div className="relative z-50">
        <Button
          onClick={onToggle}
          size="lg"
          className={cn(
            "relative h-12 w-12 rounded-full transition-all duration-300 cursor-pointer",
            isActive
              ? "bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/25"
              : "bg-primary hover:bg-primary/80 text-white shadow-lg shadow-primary/25"
          )}
        >
          {isActive ? (
            <MicOff className="h-5 w-5" />
          ) : (
            <Mic className="h-5 w-5" />
          )}
        </Button>

        {/* Pulse Animation */}
        <AnimatePresence>
          {isListening && (
            <motion.div
              key="pulse"
              initial={{ scale: 1, opacity: 0.7 }}
              animate={{ scale: 1.5, opacity: 0 }}
              exit={{ scale: 1, opacity: 0 }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 rounded-full bg-red-500"
            />
          )}
        </AnimatePresence>

        {/* Processing Indicator */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              key="processing"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="absolute -top-1 -right-1 h-3 w-3 bg-yellow-500 rounded-full"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="h-full w-full rounded-full border-2 border-yellow-500 border-t-transparent"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Audio Visualizer */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            key="visualizer"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="flex items-center space-x-1"
          >
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  scaleY: [0.5, 1, 0.5],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: "easeInOut",
                }}
                className="w-1 bg-primary rounded-full"
                style={{ height: Math.max(8, (audioLevel * 20) / 100) }}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status and Transcript */}
      <div className="flex flex-col items-center space-y-2 min-h-[60px]">
        {/* Status Badge */}
        <Badge
          variant={isActive ? (isListening ? "default" : "secondary") : "outline"}
          className={cn(
            "text-xs",
            isActive && isListening && "bg-red-600 text-white animate-pulse"
          )}
        >
          {isProcessing
            ? "Processing..."
            : isActive
            ? isListening
              ? "Listening..."
              : "Ready"
            : "Voice Off"}
        </Badge>

        {/* Transcript Display */}
        <AnimatePresence>
          {transcript && (
            <motion.div
              key="transcript"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-md"
            >
              <Card className="bg-muted/50 border-slate-700 p-3">
                <p className="text-sm text-muted-foreground text-center">
                  "{transcript}"
                </p>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Help Text */}
        {isActive && !transcript && !isProcessing && !lastResponse && whisperAvailable && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-muted-foreground text-center max-w-xs space-y-2"
          >
            <p>
              {conversationMode === 'ceo' && "🎤 Recording... Talk to the CEO!"}
              {conversationMode === 'team-meeting' && "🎤 Recording... Start your meeting topic!"}
              {conversationMode === 'task-assignment' && "🎤 Recording... Describe your task!"}
            </p>
            <p className="text-green-500 text-xs">
              🧠 Using Whisper STT + Claude CLI + ElevenLabs TTS
            </p>
          </motion.div>
        )}

        {/* Test System Button */}
        {!isActive && (!lastResponse || !whisperAvailable) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-2"
          >
            <Button
              onClick={testMicrophoneAndWhisper}
              size="sm"
              variant="outline"
              className="text-xs border-slate-600 hover:border-primary"
            >
              🔍 Test Voice System
            </Button>
          </motion.div>
        )}
      </div>


      {/* Hidden Audio Element */}
      <audio ref={audioRef} className="hidden" />
    </div>
  )
}