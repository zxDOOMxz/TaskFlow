import { cn } from '@/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
          variant === 'primary' && 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
          variant === 'secondary' && 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50 focus:ring-slate-500',
          variant === 'ghost' && 'text-slate-600 hover:bg-slate-100',
          variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
          size === 'sm' && 'px-3 py-1.5 text-sm',
          size === 'md' && 'px-4 py-2',
          size === 'lg' && 'px-6 py-3 text-lg',
          className
        )}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'
