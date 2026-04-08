import { cn } from '@/utils/cn'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const variantStyles = {
    primary: 'bg-accent text-bg-primary hover:bg-accent/90',
    secondary: 'bg-bg-secondary border border-border-subtle text-text-primary hover:bg-bg-hover',
    ghost: 'text-text-secondary hover:text-text-primary hover:bg-bg-hover',
    danger: 'bg-error text-white hover:bg-error/90',
  }

  const sizeStyles = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded font-data transition-colors',
        variantStyles[variant],
        sizeStyles[size],
        (disabled || isLoading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {!isLoading && leftIcon}
      {children}
      {!isLoading && rightIcon}
    </button>
  )
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  leftElement?: React.ReactNode
  rightElement?: React.ReactNode
}

export function Input({
  label,
  error,
  leftElement,
  rightElement,
  className,
  ...props
}: InputProps) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-xs text-text-muted mb-1">{label}</label>
      )}
      <div className="relative flex items-center">
        {leftElement && (
          <div className="absolute left-3 text-text-muted">{leftElement}</div>
        )}
        <input
          className={cn(
            'w-full px-3 py-2 bg-bg-secondary border border-border-subtle rounded text-sm text-text-primary placeholder:text-text-muted',
            'focus:outline-none focus:border-border-focus',
            leftElement && 'pl-10',
            rightElement && 'pr-10',
            error && 'border-error'
          )}
          {...props}
        />
        {rightElement && (
          <div className="absolute right-3 text-text-muted">{rightElement}</div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-xs text-error">{error}</p>
      )}
    </div>
  )
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export function Textarea({ label, error, className, ...props }: TextareaProps) {
  return (
    <div className={className}>
      {label && (
        <label className="block text-xs text-text-muted mb-1">{label}</label>
      )}
      <textarea
        className={cn(
          'w-full px-3 py-2 bg-bg-secondary border border-border-subtle rounded text-sm text-text-primary placeholder:text-text-muted',
          'focus:outline-none focus:border-border-focus',
          error && 'border-error'
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-error">{error}</p>
      )}
    </div>
  )
}

interface SelectProps {
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
  placeholder?: string
  className?: string
}

export function Select({ value, onChange, options, placeholder, className }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={cn(
        'w-full px-3 py-2 bg-bg-secondary border border-border-subtle rounded text-sm text-text-primary',
        'focus:outline-none focus:border-border-focus',
        className
      )}
    >
      {placeholder && (
        <option value="" disabled>{placeholder}</option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

interface CheckboxProps {
  id: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  className?: string
}

export function Checkbox({ id, checked, onCheckedChange, className }: CheckboxProps) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={(e) => onCheckedChange(e.target.checked)}
      className={cn(
        'w-4 h-4 text-accent bg-bg-secondary border-border-subtle rounded focus:ring-accent focus:ring-2 cursor-pointer',
        className
      )}
    />
  )
}
