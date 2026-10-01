import { cn } from '@/utils'

interface BadgeProps {
  children: React.ReactNode
  color?: string
  className?: string
}

export function Badge({ children, color, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        className
      )}
      style={{ backgroundColor: color ? `${color}20` : '#e2e8f0', color: color || '#475569' }}
    >
      {children}
    </span>
  )
}
