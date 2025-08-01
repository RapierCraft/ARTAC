'use client'

import React from 'react'

interface MarkdownMessageProps {
  content: string
  className?: string
}

export function MarkdownMessage({ content, className = '' }: MarkdownMessageProps) {
  const formatMarkdown = (text: string): React.ReactNode[] => {
    const lines = text.split('\n')
    const elements: React.ReactNode[] = []
    let key = 0

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      
      // Empty line creates paragraph break
      if (line.trim() === '') {
        if (elements.length > 0 && elements[elements.length - 1] !== 'br') {
          elements.push(<br key={`br-${key++}`} />)
        }
        continue
      }

      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h3 key={`h3-${key++}`} className="text-lg font-semibold mt-4 mb-2 first:mt-0">
            {formatInlineMarkdown(line.slice(4))}
          </h3>
        )
      } else if (line.startsWith('## ')) {
        elements.push(
          <h2 key={`h2-${key++}`} className="text-xl font-semibold mt-4 mb-2 first:mt-0">
            {formatInlineMarkdown(line.slice(3))}
          </h2>
        )
      } else if (line.startsWith('# ')) {
        elements.push(
          <h1 key={`h1-${key++}`} className="text-2xl font-bold mt-4 mb-2 first:mt-0">
            {formatInlineMarkdown(line.slice(2))}
          </h1>
        )
      }
      // Code blocks
      else if (line.trim().startsWith('```')) {
        const codeLines = []
        i++ // Skip opening ```
        while (i < lines.length && !lines[i].trim().startsWith('```')) {
          codeLines.push(lines[i])
          i++
        }
        elements.push(
          <pre key={`code-${key++}`} className="bg-muted p-3 rounded-md text-sm my-2 overflow-x-auto">
            <code>{codeLines.join('\n')}</code>
          </pre>
        )
      }
      // Lists
      else if (line.match(/^[\s]*[-*•]\s/)) {
        const listItems = []
        let j = i
        while (j < lines.length && lines[j].match(/^[\s]*[-*•]\s/)) {
          const indent = lines[j].match(/^(\s*)/)?.[1]?.length || 0
          const content = lines[j].replace(/^[\s]*[-*•]\s/, '')
          listItems.push(
            <li key={`li-${key++}`} style={{ marginLeft: `${indent * 16}px` }} className="mb-1">
              {formatInlineMarkdown(content)}
            </li>
          )
          j++
        }
        elements.push(
          <ul key={`ul-${key++}`} className="my-2 space-y-1">
            {listItems}
          </ul>
        )
        i = j - 1 // Adjust index
      }
      // Numbered lists
      else if (line.match(/^[\s]*\d+\.\s/)) {
        const listItems = []
        let j = i
        while (j < lines.length && lines[j].match(/^[\s]*\d+\.\s/)) {
          const indent = lines[j].match(/^(\s*)/)?.[1]?.length || 0
          const content = lines[j].replace(/^[\s]*\d+\.\s/, '')
          listItems.push(
            <li key={`li-${key++}`} style={{ marginLeft: `${indent * 16}px` }} className="mb-1">
              {formatInlineMarkdown(content)}
            </li>
          )
          j++
        }
        elements.push(
          <ol key={`ol-${key++}`} className="my-2 space-y-1 list-decimal list-inside">
            {listItems}
          </ol>
        )
        i = j - 1 // Adjust index
      }
      // Blockquotes
      else if (line.startsWith('> ')) {
        const quoteLines = []
        let j = i
        while (j < lines.length && lines[j].startsWith('> ')) {
          quoteLines.push(lines[j].slice(2))
          j++
        }
        elements.push(
          <blockquote key={`quote-${key++}`} className="border-l-4 border-muted-foreground/20 pl-4 my-2 text-muted-foreground italic">
            {quoteLines.map((quoteLine, idx) => (
              <div key={`quote-line-${idx}`}>{formatInlineMarkdown(quoteLine)}</div>
            ))}
          </blockquote>
        )
        i = j - 1 // Adjust index
      }
      // Regular paragraphs
      else {
        elements.push(
          <p key={`p-${key++}`} className="mb-2 last:mb-0">
            {formatInlineMarkdown(line)}
          </p>
        )
      }
    }

    return elements
  }

  const formatInlineMarkdown = (text: string): React.ReactNode => {
    // Handle mentions first
    text = text.replace(/@(\w+)/g, '<span class="text-primary font-medium bg-primary/10 px-1 rounded">@$1</span>')
    
    // Bold text
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    text = text.replace(/__(.*?)__/g, '<strong>$1</strong>')
    
    // Italic text
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>')
    text = text.replace(/_(.*?)_/g, '<em>$1</em>')
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')
    
    // Links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-primary hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
    
    // Auto-link URLs
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" class="text-primary hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
    
    // Strikethrough
    text = text.replace(/~~(.*?)~~/g, '<del>$1</del>')

    return <span dangerouslySetInnerHTML={{ __html: text }} />
  }

  return (
    <div className={`text-sm leading-relaxed ${className}`}>
      {formatMarkdown(content)}
    </div>
  )
}