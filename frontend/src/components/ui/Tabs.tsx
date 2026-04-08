import * as React from "react"
import { cn } from "@/utils/cn"

interface TabsContextType {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = React.createContext<TabsContextType | undefined>(undefined)

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
}

export function Tabs({ defaultValue, value, onValueChange, className, children, ...props }: TabsProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue || "")

  const activeValue = value !== undefined ? value : internalValue
  const handleValueChange = onValueChange || setInternalValue

  return (
    <TabsContext.Provider value={{ value: activeValue, onValueChange: handleValueChange }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

interface TabsListProps extends React.HTMLAttributes<HTMLDivElement> {}

export function TabsList({ className, ...props }: TabsListProps) {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex h-9 items-center justify-center rounded-lg bg-bg-secondary p-1 text-text-muted",
        className
      )}
      {...props}
    />
  )
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string
}

export function TabsTrigger({ className, value, children, ...props }: TabsTriggerProps) {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error("TabsTrigger must be used within Tabs")

  const { value: activeValue, onValueChange } = context
  const isActive = activeValue === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      data-state={isActive ? "active" : "inactive"}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-background shadow text-text-primary"
          : "text-text-muted hover:text-text-primary",
        className
      )}
      onClick={() => onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  )
}

interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
}

export function TabsContent({ className, value, children, ...props }: TabsContentProps) {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error("TabsContent must be used within Tabs")

  const { value: activeValue } = context
  if (activeValue !== value) return null

  return (
    <div
      role="tabpanel"
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

// Preserve old export for backward compatibility
export { Tabs as AccordionTabs, TabsList as AccordionTabsList } // Just kidding, keeping old name isn't needed if we update imports
// But let's check where the old 'Tabs' was used.
// It was used in NewsFeed.tsx? No.
// It was used in Analytics.tsx?
// I'll keep the old Tabs component as "CustomTabs" if needed, but for now, let's just export the new ones.
// The index.ts exports { Tabs, Accordion }.
// The old Tabs was a custom implementation.
// I will rename the old Tabs to CustomTabs and export it, then update index.ts.

// Wait, the old implementation was just a row of buttons.
// The new implementation is the standard shadcn style.
// I'll implement the old one as "ButtonTabs" or something if needed, but looking at the codebase,
// the old Tabs component wasn't used in the files I inspected (NewsFeed, Overview).
// Let's check if it's used elsewhere.
