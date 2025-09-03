'use client'

import * as React from 'react'

interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  children?: React.ReactNode
}

interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  className?: string
  children?: React.ReactNode
}

interface SelectValueProps {
  placeholder?: string
  className?: string
}

interface SelectContentProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
  children?: React.ReactNode
}

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  className?: string
  children?: React.ReactNode
}

const SelectContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
}>({
  value: '',
  onValueChange: () => {},
  open: false,
  setOpen: () => {}
})

export function Select({ 
  value = '', 
  onValueChange = () => {},
  children 
}: SelectProps) {
  const [open, setOpen] = React.useState(false)
  
  return (
    <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  )
}

export function SelectTrigger({ 
  children, 
  className = '',
  ...props 
}: SelectTriggerProps) {
  const { open, setOpen } = React.useContext(SelectContext)
  
  return (
    <button
      type="button"
      aria-expanded={open}
      className={`
        flex h-10 w-full items-center justify-between rounded-md border 
        border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white 
        placeholder:text-gray-500 focus:outline-none focus:ring-2 
        focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed 
        disabled:opacity-50 ${className}
      `}
      onClick={() => setOpen(!open)}
      {...props}
    >
      {children}
      <svg
        className={`h-4 w-4 opacity-50 transition-transform ${open ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
}

export function SelectValue({ 
  placeholder = 'Select an option',
  className = '' 
}: SelectValueProps) {
  const { value } = React.useContext(SelectContext)
  
  return (
    <span className={`${!value ? 'text-gray-500' : ''} ${className}`}>
      {value || placeholder}
    </span>
  )
}

export function SelectContent({ 
  children, 
  className = '',
  ...props 
}: SelectContentProps) {
  const { open, setOpen } = React.useContext(SelectContext)
  
  if (!open) return null
  
  return (
    <>
      <div 
        className="fixed inset-0 z-40" 
        onClick={() => setOpen(false)}
      />
      <div
        className={`
          absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md 
          bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 
          focus:outline-none sm:text-sm ${className}
        `}
        {...props}
      >
        {children}
      </div>
    </>
  )
}

export function SelectItem({ 
  value, 
  children, 
  className = '',
  ...props 
}: SelectItemProps) {
  const { value: selectedValue, onValueChange, setOpen } = React.useContext(SelectContext)
  const isSelected = value === selectedValue
  
  return (
    <div
      className={`
        relative cursor-pointer select-none py-2 px-3 
        ${isSelected ? 'bg-blue-50 text-blue-900' : 'text-gray-900 hover:bg-gray-100'}
        ${className}
      `}
      onClick={() => {
        onValueChange(value)
        setOpen(false)
      }}
      {...props}
    >
      {children || value}
    </div>
  )
}