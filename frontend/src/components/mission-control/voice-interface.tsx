'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface VoiceInterfaceProps {
  isActive: boolean
  onToggle: () => void
}

export function VoiceInterface({ isActive, onToggle }: VoiceInterfaceProps) {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const recognitionRef = useRef<any>(null)

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      
      const recognition = recognitionRef.current
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-US'

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event: any) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }

        setTranscript(finalTranscript || interimTranscript)

        // Process command if final result
        if (finalTranscript) {
          processVoiceCommand(finalTranscript)
        }
      }

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
        if (isActive) {
          // Restart recognition if still active
          setTimeout(() => {
            try {
              recognition.start()
            } catch (error) {
              console.error('Failed to restart recognition:', error)
            }
          }, 100)
        }
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [isActive])

  // Start/stop speech recognition
  useEffect(() => {
    if (recognitionRef.current) {
      if (isActive) {
        try {
          recognitionRef.current.start()
        } catch (error) {
          console.error('Failed to start recognition:', error)
        }
      } else {
        recognitionRef.current.stop()
        setIsListening(false)
        setTranscript('')
      }
    }
  }, [isActive])

  // Process voice command
  const processVoiceCommand = async (command: string) => {
    setIsProcessing(true)
    
    try {
      // Send command to backend
      const response = await fetch('/api/v1/voice/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command, timestamp: new Date().toISOString() }),
      })

      if (response.ok) {
        const result = await response.json()
        // Handle response (could trigger TTS or UI updates)
        console.log('Voice command processed:', result)
      }
    } catch (error) {
      console.error('Failed to process voice command:', error)
    } finally {
      setIsProcessing(false)
      setTranscript('')
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

  return (
    <div className="flex flex-col items-center space-y-3">
      {/* Main Voice Button */}
      <div className="relative">
        <Button
          onClick={onToggle}
          size="lg"
          className={cn(
            "relative h-12 w-12 rounded-full transition-all duration-300",
            isActive
              ? "bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/25"
              : "bg-artac-600 hover:bg-artac-700 text-white shadow-lg shadow-artac-500/25"
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
                className="w-1 bg-artac-500 rounded-full"
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
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-md"
            >
              <Card className="bg-slate-800/50 border-slate-700 p-3">
                <p className="text-sm text-slate-300 text-center">
                  "{transcript}"
                </p>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Help Text */}
        {isActive && !transcript && !isProcessing && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-slate-500 text-center max-w-xs"
          >
            Say commands like "Show agent status" or "Create new task"
          </motion.p>
        )}
      </div>
    </div>
  )
}