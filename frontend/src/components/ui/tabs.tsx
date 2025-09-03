'use client'

import * as React from 'react'

interface TabsProps {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children?: React.ReactNode
  className?: string
}

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
  className?: string
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  className?: string
}

const TabsContext = React.createContext<{
  value: string
  onValueChange: (value: string) => void
}>({
  value: '',
  onValueChange: () => {}
})

export function Tabs({ 
  defaultValue = '', 
  value: controlledValue,
  onValueChange,
  children,
  className = ''
}: TabsProps) {
  const [uncontrolledValue, setUncontrolledValue] = React.useState(defaultValue)
  const value = controlledValue ?? uncontrolledValue
  const handleValueChange = onValueChange ?? setUncontrolledValue
  
  return (
    <TabsContext.Provider value={{ value, onValueChange: handleValueChange }}>
      <div className={`w-full ${className}`}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

export function TabsList({ 
  children, 
  className = '',
  ...props 
}: TabsListProps) {
  return (
    <div 
      className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500 ${className}`}
      role="tablist"
      {...props}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({ 
  value, 
  children, 
  className = '',
  ...props 
}: TabsTriggerProps) {
  const { value: selectedValue, onValueChange } = React.useContext(TabsContext)
  const isSelected = value === selectedValue
  
  return (
    <button
      role="tab"
      aria-selected={isSelected}
      className={`
        inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 
        text-sm font-medium ring-offset-white transition-all 
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 
        focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50
        ${isSelected 
          ? 'bg-white text-gray-900 shadow-sm' 
          : 'text-gray-500 hover:text-gray-900'}
        ${className}
      `}
      onClick={() => onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  )
}

export function TabsContent({ 
  value, 
  children, 
  className = '',
  ...props 
}: TabsContentProps) {
  const { value: selectedValue } = React.useContext(TabsContext)
  
  if (value !== selectedValue) return null
  
  return (
    <div
      role="tabpanel"
      className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}