import { React } from 'react';
import { cn } from "@/utils/cn";
import {
  Search,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Globe,
  Activity,
  PieChart,
  BarChart3,
  ArrowUpRight,
  Clock,
  Star,
  Sparkles,
} from "lucide-react";

// Clean Theme (No Glowing Effects)
const CLEAN_THEME = {
  colors: {
    primary: "#2563eb",
    secondary: "#64748b",
    success: "#16a34a",
    danger: "#dc2626",
    warning: "#d97706",
    info: "#0891b2",
    bgPrimary: "#ffffff",
    bgSecondary: "#f8fafc",
    bgTertiary: "#f1f5f9",
    bgCard: "#ffffff",
    bgHover: "#f8fafc",
    bgActive: "#e2e8f0",
    textPrimary: "#1e293b",
    textSecondary: "#64748b",
    textMuted: "#94a3b8",
    textInverse: "#ffffff",
    borderSubtle: "#f1f5f9",
    borderDefault: "#e2e8f0",
    borderStrong: "#cbd5e1",
    borderFocus: "#3b82f6",
  },
  font: {
    display: '"Inter", -apple-system, sans-serif',
    body: '"Inter", -apple-system, sans-serif',
    mono: '"JetBrains Mono", monospace',
  },
  shadows: {
    card: "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)",
    cardHover: "0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06)",
    button: "0 1px 2px rgba(0, 0, 0, 0.05)",
  },
};

// Clean Card Component
export function CleanCard({ children, className, hover = true, padding = "md" }: { 
  children: React.ReactNode; 
  className?: string; 
  hover?: boolean;
  padding?: "sm" | "md" | "lg";
}) {
  const paddingClass = {
    sm: "p-4",
    md: "p-6",
    lg: "p-8"
  }[padding];

  return (
    <div
      className={cn(
        "bg-white border rounded-lg transition-all duration-200",
        hover && "hover:shadow-md",
        paddingClass,
        className
      )}
      style={{
        borderColor: CLEAN_THEME.colors.borderDefault,
        boxShadow: CLEAN_THEME.colors.shadowCard,
      }}
    >
      {children}
    </div>
  );
}

// Clean Button Component
export function CleanButton({ children, onClick, active, className, icon: Icon, variant = "primary", size = "md" }: { 
  children: React.ReactNode; 
  onClick?: () => void; 
  active?: boolean;
  className?: string;
  icon?: React.ElementType;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}) {
  const baseClass = "inline-flex items-center gap-2 font-medium transition-all duration-200";
  const sizeClass = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base"
  }[size];

  const variantClass = {
    primary: active 
      ? "bg-blue-600 text-white" 
      : "bg-blue-600 text-white hover:bg-blue-700",
    secondary: active 
      ? "bg-gray-100 text-gray-900 border-gray-300" 
      : "bg-gray-100 text-gray-900 hover:bg-gray-200 border-gray-300",
    outline: active 
      ? "bg-blue-50 text-blue-600 border-blue-600" 
      : "bg-white text-gray-700 hover:bg-gray-50 border-gray-300",
    ghost: active 
      ? "bg-gray-100 text-gray-900" 
      : "text-gray-600 hover:bg-gray-100"
  }[variant];

  return (
    <button
      onClick={onClick}
      className={cn(baseClass, sizeClass, variantClass, "rounded-md", className)}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
}

// Stock Change Component
export function StockChange({ change, percent }: { change: string; percent: string }) {
  const isPositive = !change?.includes("-") && !percent?.includes("-");
  const color = isPositive ? CLEAN_THEME.colors.success : CLEAN_THEME.colors.danger;
  
  return (
    <div className="flex items-center gap-1">
      {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
      <span className="font-semibold" style={{ color }}>{change || percent}</span>
    </div>
  );
}

// Stock Card Component
export function StockCard({ item, onClick, className }: { 
  item: any; 
  onClick?: () => void; 
  className?: string;
}) {
  const isPositive = !item.change?.includes("-") && !item.change_percent?.includes("-");
  const isIndian = item.exchange === "NSE" || item.ticker?.endsWith(".NS");
  
  return (
    <CleanCard 
      className={cn("cursor-pointer", className)}
      hover
      padding="md"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 
              className="font-bold text-lg"
              style={{ 
                fontFamily: CLEAN_THEME.font.mono, 
                color: CLEAN_THEME.colors.textPrimary 
              }}
            >
              {item.ticker || item.symbol}
            </h3>
            {isIndian && (
              <span 
                className="text-xs px-2 py-1 rounded-md font-medium"
                style={{
                  backgroundColor: CLEAN_THEME.colors.bgTertiary,
                  color: CLEAN_THEME.colors.textSecondary,
                }}
              >
                🇮🇳 NSE
              </span>
            )}
          </div>
          <p 
            className="text-sm line-clamp-1"
            style={{ color: CLEAN_THEME.colors.textMuted }}
          >
            {item.name}
          </p>
        </div>
        <div className="px-2 py-1 rounded-md text-xs font-medium bg-green-50 text-green-600">
          Live
        </div>
      </div>
      
      <div className="flex items-end justify-between">
        <div>
          <p 
            className="text-2xl font-bold"
            style={{ 
              fontFamily: CLEAN_THEME.font.mono, 
              color: CLEAN_THEME.colors.textPrimary 
            }}
          >
            {isIndian ? "₹" : "$"}{item.price || item.value || "0.00"}
          </p>
          <StockChange change={item.change} percent={item.change_percent} />
        </div>
        
        {item.volume && (
          <div className="text-right">
            <p 
              className="text-xs"
              style={{ color: CLEAN_THEME.colors.textMuted }}
            >
              Volume
            </p>
            <p 
              className="text-sm font-semibold"
              style={{ 
                fontFamily: CLEAN_THEME.font.mono,
                color: CLEAN_THEME.colors.textSecondary 
              }}
            >
              {item.volume}
            </p>
          </div>
        )}
      </div>
    </CleanCard>
  );
}

// Header Component
export function FinanceHeader({ title, subtitle, icon: Icon }: { 
  title: string; 
  subtitle: string; 
  icon: React.ElementType;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-4 mb-4">
        <div 
          className="w-12 h-12 rounded-lg flex items-center justify-center"
          style={{ 
            backgroundColor: CLEAN_THEME.colors.primary,
          }}
        >
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 
            className="text-3xl font-bold"
            style={{ 
              fontFamily: CLEAN_THEME.font.display, 
              color: CLEAN_THEME.colors.textPrimary 
            }}
          >
            {title}
          </h1>
          <p style={{ color: CLEAN_THEME.colors.textSecondary, fontFamily: CLEAN_THEME.font.body }}>
            {subtitle}
          </p>
        </div>
      </div>
    </div>
  );
}

// Search Bar Component
export function SearchBar({ searchQuery, setSearchQuery, onSearch, onRefresh, loading }: {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSearch: () => void;
  onRefresh: () => void;
  loading: boolean;
}) {
  return (
    <div className="flex gap-3 mb-6">
      <div className="flex-1 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search stocks, ETFs, indices..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          className="w-full pl-10 pr-4 py-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          style={{ 
            borderColor: CLEAN_THEME.colors.borderDefault,
            color: CLEAN_THEME.colors.textPrimary,
            fontFamily: CLEAN_THEME.font.body,
          }}
        />
      </div>
      <CleanButton onClick={onSearch} icon={Search} variant="primary">
        Search
      </CleanButton>
      <CleanButton 
        onClick={onRefresh} 
        icon={RefreshCw} 
        variant="outline"
        className="px-3"
      >
        <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
      </CleanButton>
    </div>
  );
}

// Navigation Tabs Component
export function NavigationTabs({ activeTab, setActiveTab, tabs }: {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  tabs: Array<{ id: string; label: string; icon: React.ElementType }>;
}) {
  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "py-2 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === tab.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            )}
          >
            <div className="flex items-center gap-2">
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </div>
          </button>
        ))}
      </nav>
    </div>
  );
}

// Auto Refresh Controls Component
export function AutoRefreshControls({ autoRefresh, setAutoRefresh, lastRefreshed }: {
  autoRefresh: boolean;
  setAutoRefresh: (refresh: boolean) => void;
  lastRefreshed: Date;
}) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3 text-sm text-gray-500">
        <Clock className="w-4 h-4" />
        <span>Last updated: {lastRefreshed.toLocaleTimeString()}</span>
        {autoRefresh && (
          <span className="flex items-center gap-2 px-3 py-1 rounded-md text-xs font-medium bg-green-50 text-green-600">
            <RefreshCw className="w-3 h-3 animate-spin" />
            Auto-refresh ON
          </span>
        )}
      </div>
      
      <CleanButton
        onClick={() => setAutoRefresh(!autoRefresh)}
        variant="outline"
        size="sm"
      >
        {autoRefresh ? "🔄 Auto-refresh ON" : "⏸️ Auto-refresh OFF"}
      </CleanButton>
    </div>
  );
}

// Loading State Component
export function LoadingState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-t-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
}

// Empty State Component
export function EmptyState({ title, message, onRefresh }: { 
  title: string; 
  message: string; 
  onRefresh?: () => void;
}) {
  return (
    <div className="col-span-full">
      <CleanCard padding="lg" className="text-center">
        <div className="text-6xl mb-4">📊</div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {title}
        </h3>
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          {message}
        </p>
        {onRefresh && (
          <CleanButton onClick={onRefresh} icon={RefreshCw} variant="primary">
            Refresh Data
          </CleanButton>
        )}
      </CleanCard>
    </div>
  );
}

// Section Title Component
export function SectionTitle({ title, icon: Icon }: { 
  title: string; 
  icon: React.ElementType;
}) {
  return (
    <div className="flex items-center gap-2 mb-6">
      <Icon className="w-5 h-5 text-blue-600" />
      <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
    </div>
  );
}

export { CLEAN_THEME };
