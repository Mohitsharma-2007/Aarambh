import { cn } from '@/utils/cn'

interface TableProps {
  children: React.ReactNode
  className?: string
}

export function Table({ children, className }: TableProps) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full text-sm">
        {children}
      </table>
    </div>
  )
}

interface TableHeaderProps {
  children: React.ReactNode
}

export function TableHeader({ children }: TableHeaderProps) {
  return (
    <thead className="border-b border-border-subtle">
      {children}
    </thead>
  )
}

interface TableBodyProps {
  children: React.ReactNode
}

export function TableBody({ children }: TableBodyProps) {
  return (
    <tbody className="divide-y divide-border-subtle">
      {children}
    </tbody>
  )
}

interface TableRowProps {
  children: React.ReactNode
  onClick?: () => void
  className?: string
}

export function TableRow({ children, onClick, className }: TableRowProps) {
  return (
    <tr
      className={cn(
        onClick && 'cursor-pointer hover:bg-bg-hover transition-colors',
        className
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  )
}

interface TableHeadProps {
  children: React.ReactNode
  className?: string
}

export function TableHead({ children, className }: TableHeadProps) {
  return (
    <th className={cn(
      'px-4 py-3 text-left text-xs font-data font-semibold text-text-muted uppercase tracking-wider',
      className
    )}>
      {children}
    </th>
  )
}

interface TableCellProps {
  children: React.ReactNode
  className?: string
  colSpan?: number
}

export function TableCell({ children, className, colSpan }: TableCellProps) {
  return (
    <td colSpan={colSpan} className={cn('px-4 py-3 text-text-secondary', className)}>
      {children}
    </td>
  )
}

interface DataTableProps<T> {
  data: T[]
  columns: {
    key: keyof T
    header: string
    render?: (value: T[keyof T], row: T) => React.ReactNode
    className?: string
  }[]
  onRowClick?: (row: T) => void
  className?: string
}

export function DataTable<T extends Record<string, unknown>>({
  data,
  columns,
  onRowClick,
  className,
}: DataTableProps<T>) {
  return (
    <Table className={className}>
      <TableHeader>
        <TableRow>
          {columns.map((col) => (
            <TableHead key={String(col.key)} className={col.className}>
              {col.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row, i) => (
          <TableRow key={i} onClick={() => onRowClick?.(row)}>
            {columns.map((col) => (
              <TableCell key={String(col.key)} className={col.className}>
                {col.render
                  ? col.render(row[col.key], row)
                  : String(row[col.key] ?? '')}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
