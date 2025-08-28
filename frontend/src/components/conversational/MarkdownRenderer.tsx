'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks]}
        components={{
          // Table styling
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full border-collapse border border-gray-300 text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-100">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="bg-white divide-y divide-gray-200">
              {children}
            </tbody>
          ),
          th: ({ children }) => (
            <th className="border border-gray-300 px-4 py-2 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-gray-300 px-4 py-2 text-sm text-gray-700">
              {children}
            </td>
          ),
          // Links styling
          a: ({ href, children }) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {children}
            </a>
          ),
          // Headings styling
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-gray-900 mb-3 mt-6 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-gray-900 mb-2 mt-5 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-md font-semibold text-gray-900 mb-2 mt-4 first:mt-0">
              {children}
            </h3>
          ),
          // Lists styling
          ul: ({ children }) => (
            <ul className="list-disc list-inside space-y-1 my-3 text-gray-700">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside space-y-1 my-3 text-gray-700">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-sm text-gray-700 leading-relaxed">
              {children}
            </li>
          ),
          // Paragraphs
          p: ({ children }) => (
            <p className="text-sm text-gray-700 leading-relaxed mb-3">
              {children}
            </p>
          ),
          // Code blocks
          pre: ({ children }) => (
            <pre className="bg-gray-100 rounded-md p-3 overflow-x-auto my-3 text-xs">
              {children}
            </pre>
          ),
          code: ({ inline, children }) => 
            inline ? (
              <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono text-gray-800">
                {children}
              </code>
            ) : (
              <code className="text-gray-800 font-mono">
                {children}
              </code>
            ),
          // Blockquotes
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-400 pl-4 py-2 my-3 bg-blue-50 text-sm text-gray-700 italic">
              {children}
            </blockquote>
          ),
          // Horizontal rules
          hr: () => (
            <hr className="border-gray-300 my-6" />
          ),
          // Strong/Bold
          strong: ({ children }) => (
            <strong className="font-semibold text-gray-900">
              {children}
            </strong>
          ),
          // Emphasis/Italic
          em: ({ children }) => (
            <em className="italic text-gray-700">
              {children}
            </em>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}