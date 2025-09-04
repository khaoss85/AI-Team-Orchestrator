'use client'

import * as React from 'react'

interface DialogProps {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  children?: React.ReactNode
}

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  className?: string
}

interface DialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  className?: string
}

interface DialogTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children?: React.ReactNode
  className?: string
}

interface DialogDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children?: React.ReactNode
  className?: string
}

const DialogContext = React.createContext<{
  open: boolean
  onOpenChange: (open: boolean) => void
}>({
  open: false,
  onOpenChange: () => {}
})

export function Dialog({ open = false, onOpenChange = () => {}, children }: DialogProps) {
  return (
    <DialogContext.Provider value={{ open, onOpenChange }}>
      {children}
    </DialogContext.Provider>
  )
}

interface DialogTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  children?: React.ReactNode
}

export function DialogTrigger({ children, asChild = false, ...props }: DialogTriggerProps) {
  const { onOpenChange } = React.useContext(DialogContext)
  
  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    props.onClick?.(e)
    onOpenChange(true)
  }, [props, onOpenChange])

  // When asChild is true, clone the child element and add onClick handler
  if (asChild && React.isValidElement(children)) {
    const childElement = children as React.ReactElement<{onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void}>
    return React.cloneElement(childElement, {
      onClick: (e: React.MouseEvent<HTMLButtonElement>) => {
        // Call the child's existing onClick handler if it exists
        if (childElement.props.onClick) {
          childElement.props.onClick(e)
        }
        handleClick(e)
      }
    })
  }
  
  // Default button rendering when asChild is false
  return (
    <button
      {...props}
      onClick={handleClick}
    >
      {children}
    </button>
  )
}

export function DialogContent({ 
  children, 
  className = '',
  ...props 
}: DialogContentProps) {
  const { open, onOpenChange } = React.useContext(DialogContext)
  
  if (!open) return null
  
  return (
    <>
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-50"
        onClick={() => onOpenChange(false)}
      />
      <div 
        className={`fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl p-6 z-50 max-w-md w-full max-h-[90vh] overflow-y-auto ${className}`}
        {...props}
      >
        <button
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          onClick={() => onOpenChange(false)}
        >
          ✕
        </button>
        {children}
      </div>
    </>
  )
}

export function DialogHeader({ 
  children, 
  className = '',
  ...props 
}: DialogHeaderProps) {
  return (
    <div className={`mb-4 ${className}`} {...props}>
      {children}
    </div>
  )
}

export function DialogTitle({ 
  children, 
  className = '',
  ...props 
}: DialogTitleProps) {
  return (
    <h2 className={`text-lg font-semibold ${className}`} {...props}>
      {children}
    </h2>
  )
}

export function DialogDescription({ 
  children, 
  className = '',
  ...props 
}: DialogDescriptionProps) {
  return (
    <p className={`text-sm text-gray-500 mt-2 ${className}`} {...props}>
      {children}
    </p>
  )
}