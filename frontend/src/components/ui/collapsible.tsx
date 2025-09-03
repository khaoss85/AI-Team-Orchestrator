'use client'

import * as React from 'react'

interface CollapsibleProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children?: React.ReactNode
  className?: string
}

interface CollapsibleTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  className?: string
}

interface CollapsibleContentProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

const CollapsibleContext = React.createContext<{
  open: boolean
  onOpenChange: (open: boolean) => void
}>({
  open: false,
  onOpenChange: () => {}
})

export function Collapsible({ 
  open: controlledOpen,
  onOpenChange,
  children,
  className = ''
}: CollapsibleProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(false)
  const open = controlledOpen ?? uncontrolledOpen
  const handleOpenChange = onOpenChange ?? setUncontrolledOpen
  
  return (
    <CollapsibleContext.Provider value={{ open, onOpenChange: handleOpenChange }}>
      <div className={className}>
        {children}
      </div>
    </CollapsibleContext.Provider>
  )
}

export function CollapsibleTrigger({ 
  children, 
  asChild,
  className = '',
  ...props 
}: CollapsibleTriggerProps) {
  const { open, onOpenChange } = React.useContext(CollapsibleContext)
  
  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    props.onClick?.(e)
    onOpenChange(!open)
  }, [open, onOpenChange, props])
  
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as any, {
      onClick: handleClick,
      'aria-expanded': open,
      'data-state': open ? 'open' : 'closed'
    })
  }
  
  return (
    <button
      type="button"
      aria-expanded={open}
      data-state={open ? 'open' : 'closed'}
      className={className}
      onClick={handleClick}
      {...props}
    >
      {children}
    </button>
  )
}

export function CollapsibleContent({ 
  children, 
  className = '',
  ...props 
}: CollapsibleContentProps) {
  const { open } = React.useContext(CollapsibleContext)
  
  if (!open) return null
  
  return (
    <div
      data-state={open ? 'open' : 'closed'}
      className={className}
      {...props}
    >
      {children}
    </div>
  )
}