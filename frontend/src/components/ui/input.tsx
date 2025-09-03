'use client'

import * as React from 'react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', error, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={`
          flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm 
          ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium 
          placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 
          focus-visible:ring-blue-500 focus-visible:ring-offset-2 
          disabled:cursor-not-allowed disabled:opacity-50
          ${error ? 'border-red-500 focus-visible:ring-red-500' : ''}
          ${className}
        `}
        ref={ref}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'

export { Input }