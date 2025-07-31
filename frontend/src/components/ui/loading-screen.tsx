'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

const loadingMessages = [
  'Initializing ARTAC System...',
  'Connecting to Agent Network...',
  'Loading RAG Knowledge Base...',
  'Establishing Claude Code Sessions...',
  'Preparing Mission Control...',
  'System Ready!'
]

export function LoadingScreen() {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => {
        if (prev < loadingMessages.length - 1) {
          return prev + 1
        }
        return prev
      })
    }, 800)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex min-h-screen items-center justify-center mission-control-bg">
      <div className="flex flex-col items-center space-y-8">
        {/* ARTAC Logo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center space-y-4"
        >
          <div className="relative">
            <div className="text-6xl font-bold gradient-text">ARTAC</div>
            <div className="absolute -inset-1 bg-gradient-to-r from-artac-500 to-artac-700 rounded-lg blur opacity-25"></div>
          </div>
          <div className="text-lg text-muted-foreground">
            Agentic Runtime & Task Allocation Controller
          </div>
        </motion.div>

        {/* Loading Animation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col items-center space-y-6"
        >
          {/* Circular Progress */}
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="4"
                fill="transparent"
                className="text-muted-foreground/20"
              />
              <motion.circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="4"
                fill="transparent"
                strokeLinecap="round"
                className="text-artac-500"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: (currentMessageIndex + 1) / loadingMessages.length }}
                transition={{ duration: 0.8, ease: "easeInOut" }}
                style={{
                  strokeDasharray: "251.2",
                  strokeDashoffset: 0,
                }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-3 h-3 bg-artac-500 rounded-full"
              />
            </div>
          </div>

          {/* Loading Message */}
          <motion.div
            key={currentMessageIndex}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-center"
          >
            <div className="text-lg font-medium text-foreground">
              {loadingMessages[currentMessageIndex]}
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              Step {currentMessageIndex + 1} of {loadingMessages.length}
            </div>
          </motion.div>
        </motion.div>

        {/* Loading Dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="flex space-x-2"
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
              }}
              className="w-3 h-3 bg-artac-500 rounded-full"
            />
          ))}
        </motion.div>

        {/* System Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="text-center text-xs text-muted-foreground space-y-1"
        >
          <div>Mission Control Dashboard v0.1.0-alpha</div>
          <div>Powered by Claude 4 Sonnet</div>
        </motion.div>
      </div>
    </div>
  )
}