'use client'

import React from 'react'
import { ConversationMessage } from './types'

interface ConversationBubbleProps {
  message: ConversationMessage
}

export default function ConversationBubble({ message }: ConversationBubbleProps) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`
        max-w-xs lg:max-w-md px-4 py-3 rounded-2xl
        ${isUser 
          ? 'bg-blue-600 text-white ml-auto' 
          : 'bg-white border border-gray-200 shadow-sm'
        }
      `}>
        {/* Message Header */}
        {!isUser && (
          <div className="flex items-center mb-2">
            <div className="flex items-center space-x-2">
              <span className="text-lg">🤖</span>
              <span className="text-xs font-medium text-gray-500">
                {message.metadata?.teamMember || 'AI Team'}
              </span>
              {message.metadata?.confidence && (
                <span className="text-xs text-gray-400">
                  ({Math.round(message.metadata.confidence * 100)}%)
                </span>
              )}
            </div>
          </div>
        )}

        {/* Message Content */}
        <div className={`text-sm whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-900'}`}>
          {message.content}
        </div>

        {/* Working On Indicator */}
        {message.metadata?.workingOn && message.metadata.workingOn.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <div className="text-xs text-gray-500 mb-1">Working on:</div>
            <div className="flex flex-wrap gap-1">
              {message.metadata.workingOn.map((item, index) => (
                <span 
                  key={index}
                  className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Attachments */}
        {message.metadata?.attachments && message.metadata.attachments.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.metadata.attachments.map((attachment) => (
              <AttachmentPreview key={attachment.id} attachment={attachment} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-400'}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  )
}

// Attachment Preview Component
interface AttachmentPreviewProps {
  attachment: {
    id: string
    title: string
    type: string
    preview?: string
  }
}

function AttachmentPreview({ attachment }: AttachmentPreviewProps) {
  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'document': return '📄'
      case 'image': return '🖼️'
      case 'spreadsheet': return '📊'
      case 'presentation': return '📈'
      case 'deliverable': return '📦'
      case 'strategy': return '🎯'
      case 'calendar': return '📅'
      default: return '📎'
    }
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:bg-gray-100 cursor-pointer transition-colors">
      <div className="flex items-start space-x-2">
        <span className="text-lg flex-shrink-0">
          {getTypeIcon(attachment.type)}
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {attachment.title}
          </div>
          <div className="text-xs text-gray-500 capitalize">
            {attachment.type}
          </div>
          {attachment.preview && (
            <div className="text-xs text-gray-600 mt-1 line-clamp-2">
              {attachment.preview}
            </div>
          )}
        </div>
        <div className="text-xs text-blue-600 hover:text-blue-700">
          View →
        </div>
      </div>
    </div>
  )
}