'use client';

import React, { useState, useEffect } from 'react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  height?: string;
}

// Simple code editor component - in a real app, you would use Monaco Editor or a similar library
const CodeEditor: React.FC<CodeEditorProps> = ({ 
  value, 
  onChange, 
  language = 'python',
  height = '400px'
}) => {
  const [isFocused, setIsFocused] = useState(false);
  
  // Apply simple syntax highlighting for Python (very basic)
  const highlightPython = (code: string) => {
    // This is a very simple implementation
    // In a real app, use a proper syntax highlighting library
    return code
      .replace(/\b(def|class|import|from|return|async|await|if|else|for|while|try|except|with|as|in|not|and|or)\b/g, '<span class="text-purple-600">$1</span>')
      .replace(/\b(True|False|None)\b/g, '<span class="text-blue-600">$1</span>')
      .replace(/(["'])(.*?)\1/g, '<span class="text-green-600">$1$2$1</span>')
      .replace(/#(.*)/g, '<span class="text-gray-500">#$1</span>');
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };
  
  return (
    <div className={`relative border ${isFocused ? 'border-indigo-500' : 'border-gray-300'} rounded-md transition`}>
      <div className="absolute top-0 right-0 bg-gray-100 px-3 py-1 text-xs text-gray-600 rounded-bl-md rounded-tr-md">
        {language}
      </div>
      
      {/* Syntax highlighted preview (read-only) */}
      {!isFocused && (
        <div 
          className="font-mono text-sm p-4 overflow-auto whitespace-pre"
          style={{ height }}
          onClick={() => setIsFocused(true)}
          dangerouslySetInnerHTML={{ __html: highlightPython(value) }}
        />
      )}
      
      {/* Actual editable textarea */}
      {isFocused && (
        <textarea
          value={value}
          onChange={handleChange}
          onBlur={() => setIsFocused(false)}
          autoFocus
          className="font-mono text-sm p-4 w-full outline-none resize-none"
          style={{ height }}
        />
      )}
    </div>
  );
};

export default CodeEditor;