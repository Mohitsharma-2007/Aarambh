import { useEffect, useState, useCallback } from "react";
import { unifiedAPI } from "@/api/unified";
import { cn } from "@/utils/cn";
import { Pagination } from "@/components/Pagination";
import { LiveTVChannel } from "@/components/YouTubeEmbed";
import { LiveTVChannelEnhanced } from "@/components/LiveTVChannelEnhanced";
import { NewsCard } from "@/components/NewsCard";
import { locationService, useLocation } from "@/utils/location";
import {
  Search,
  RefreshCw,
  Clock,
  ExternalLink,
  Newspaper,
  Globe,
  Briefcase,
  Cpu,
  Tv,
  Trophy,
  FlaskConical,
  HeartPulse,
  MapPin,
  TrendingUp,
  Radio,
  AlertCircle,
  Sparkles,
  Loader2,
  Zap,
  Activity,
  BarChart3,
  Eye,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

// Bento Design System — shared tokens
import { BENTO } from "@/styles/bento";

// Map DARK_THEME to BENTO for backward compatibility
const DARK_THEME = {
  colors: {
    primary: BENTO.colors.primary,
    secondary: BENTO.colors.bgSecondary,
    accent: BENTO.colors.accent,
    success: BENTO.colors.success,
    warning: BENTO.colors.warning,
    danger: BENTO.colors.danger,
    info: BENTO.colors.info,
    bgPrimary: BENTO.colors.bgPrimary,
    bgSecondary: BENTO.colors.bgSecondary,
    bgTertiary: BENTO.colors.bgTertiary,
    bgCard: BENTO.colors.bgCard,
    bgHover: BENTO.colors.bgHover,
    bgActive: BENTO.colors.bgActive,
    textPrimary: BENTO.colors.textPrimary,
    textSecondary: BENTO.colors.textSecondary,
    textMuted: BENTO.colors.textMuted,
    textInverse: BENTO.colors.textInverse,
    borderSubtle: BENTO.colors.borderSubtle,
    borderDefault: BENTO.colors.borderDefault,
    borderStrong: BENTO.colors.borderStrong,
    borderFocus: BENTO.colors.borderFocus,
    gradientPrimary: BENTO.gradient.primary,
    gradientCard: BENTO.gradient.card,
    gradientHover: `linear-gradient(135deg, rgba(250, 212, 192, 0.08) 0%, rgba(128, 161, 193, 0.08) 100%)`,
  },
  font: BENTO.font,
  spacing: [4, 8, 12, 16, 24, 32, 48, 64],
  shadows: BENTO.shadow,
};

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  source: string;
  published: string;
  url: string;
  category?: string;
  sentiment?: { label: string; score: number };
  entities?: { countries?: string[]; organizations?: string[] };
}

const CATEGORIES = [
  { id: "headlines", label: "Headlines", icon: Newspaper, color: DARK_THEME.colors.primary },
  { id: "finance", label: "Finance", icon: Briefcase, color: DARK_THEME.colors.success },
  { id: "world", label: "World", icon: Globe, color: DARK_THEME.colors.info },
  { id: "tech", label: "Technology", icon: Cpu, color: DARK_THEME.colors.warning },
  { id: "health", label: "Health", icon: HeartPulse, color: DARK_THEME.colors.danger },
  { id: "sports", label: "Sports", icon: Trophy, color: "#8B5CF6" },
  { id: "science", label: "Science", icon: FlaskConical, color: DARK_THEME.colors.success },
  { id: "tv", label: "Live TV", icon: Tv, color: DARK_THEME.colors.accent },
];

function timeAgo(dateStr: string): string {
  if (!dateStr) return "Recently";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return `${Math.floor(diff / 60000)}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function getSentimentColor(label: string): string {
  switch (label?.toLowerCase()) {
    case "positive": return DARK_THEME.colors.success;
    case "negative": return DARK_THEME.colors.danger;
    default: return DARK_THEME.colors.warning;
  }
}

// Dark Card Component with isometric effects
function DarkCard({ children, className, hover = true, glow = false }: {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border transition-all duration-300",
        hover && "hover:transform hover:-translate-y-1 hover:scale-[1.02]",
        className
      )}
      style={{
        background: DARK_THEME.colors.gradientCard,
        borderColor: DARK_THEME.colors.borderDefault,
        boxShadow: hover ? DARK_THEME.shadows.card : DARK_THEME.shadows.card,
        backdropFilter: "blur(10px)",
      }}
    >
      {/* Isometric background pattern */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.05) 35px, rgba(255,255,255,.05) 70px),
            repeating-linear-gradient(-45deg, transparent, transparent 35px, rgba(255,255,255,.03) 35px, rgba(255,255,255,.03) 70px)
          `,
        }}
      />

      {/* Glow effect */}
      {glow && (
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: DARK_THEME.colors.gradientHover,
            filter: "blur(20px)",
          }}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}

// Dark Button Component
function DarkButton({
  children,
  onClick,
  active,
  className,
  icon: Icon,
  variant = "primary",
  size = "md",
  disabled = false
}: {
  children?: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
  className?: string;
  icon?: React.ElementType;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
}) {
  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  const variantStyles = {
    primary: {
      background: active ? DARK_THEME.colors.gradientPrimary : "transparent",
      border: `1px solid ${DARK_THEME.colors.primary}`,
      color: active ? DARK_THEME.colors.textInverse : DARK_THEME.colors.primary,
      boxShadow: active ? DARK_THEME.shadows.glow : "none",
    },
    secondary: {
      background: active ? DARK_THEME.colors.bgActive : "transparent",
      border: `1px solid ${DARK_THEME.colors.borderDefault}`,
      color: DARK_THEME.colors.textSecondary,
      boxShadow: "none",
    },
    ghost: {
      background: "transparent",
      border: `1px solid transparent`,
      color: DARK_THEME.colors.textSecondary,
      boxShadow: "none",
    },
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "rounded-xl font-medium transition-all duration-200 flex items-center gap-2",
        "hover:transform hover:-translate-y-0.5",
        disabled && "opacity-50 cursor-not-allowed",
        !disabled && "hover:transform hover:-translate-y-0.5",
        sizeClasses[size],
        className
      )}
      style={{
        ...variantStyles[variant],
        fontFamily: DARK_THEME.font.primary,
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
}

// Isometric Background Animation Component
function IsometricBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {/* Floating isometric shapes */}
      <div className="absolute top-20 left-10 w-32 h-32 opacity-5 animate-pulse">
        <div
          className="w-full h-full transform rotate-45"
          style={{
            background: DARK_THEME.colors.gradientPrimary,
            clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
          }}
        />
      </div>

      <div className="absolute top-40 right-20 w-24 h-24 opacity-5 animate-bounce">
        <div
          className="w-full h-full"
          style={{
            background: DARK_THEME.colors.gradientHover,
            clipPath: "polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%)",
          }}
        />
      </div>

      <div className="absolute bottom-40 left-1/4 w-40 h-40 opacity-5 animate-pulse">
        <div
          className="w-full h-full transform rotate-12"
          style={{
            background: DARK_THEME.colors.gradientCard,
            clipPath: "polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%)",
          }}
        />
      </div>

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-3"
        style={{
          backgroundImage: `
            linear-gradient(${DARK_THEME.colors.borderSubtle} 1px, transparent 1px),
            linear-gradient(90deg, ${DARK_THEME.colors.borderSubtle} 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      />
    </div>
  );
}

// Enhanced Pagination Component
function EnhancedPagination({
  currentPage,
  totalPages,
  onPageChange,
  totalItems,
  itemsPerPage,
  className
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalItems: number;
  itemsPerPage: number;
  className?: string;
}) {
  const pages = [];
  const maxVisiblePages = 5;

  let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
  let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

  if (endPage - startPage < maxVisiblePages - 1) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className={cn("flex items-center justify-between", className)}>
      <div className="text-sm" style={{ color: DARK_THEME.colors.textMuted }}>
        Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} articles
      </div>

      <div className="flex items-center gap-2">
        <DarkButton
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          variant="ghost"
          size="sm"
          icon={ChevronLeft}
        />

        {startPage > 1 && (
          <>
            <DarkButton
              onClick={() => onPageChange(1)}
              active={currentPage === 1}
              variant="secondary"
              size="sm"
            >
              1
            </DarkButton>
            {startPage > 2 && (
              <span style={{ color: DARK_THEME.colors.textMuted }}>...</span>
            )}
          </>
        )}

        {pages.map((page) => (
          <DarkButton
            key={page}
            onClick={() => onPageChange(page)}
            active={currentPage === page}
            variant={currentPage === page ? "primary" : "secondary"}
            size="sm"
          >
            {page}
          </DarkButton>
        ))}

        {endPage < totalPages && (
          <>
            {endPage < totalPages - 1 && (
              <span style={{ color: DARK_THEME.colors.textMuted }}>...</span>
            )}
            <DarkButton
              onClick={() => onPageChange(totalPages)}
              active={currentPage === totalPages}
              variant="secondary"
              size="sm"
            >
              {totalPages}
            </DarkButton>
          </>
        )}

        <DarkButton
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          variant="ghost"
          size="sm"
          icon={ChevronRight}
        />
      </div>
    </div>
  );
}

export default function NewsPage() {
  const [activeCategory, setActiveCategory] = useState("headlines");
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [featuredArticles, setFeaturedArticles] = useState<NewsArticle[]>([]);
  const [warStreams, setWarStreams] = useState<any[]>([]);
  const [tvChannels, setTvChannels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [initialLoading, setInitialLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState(new Date());
  const [error, setError] = useState<string | null>(null);

  // Location detection
  const { location, loading: locationLoading } = useLocation();
  const [userCountry, setUserCountry] = useState<string>("");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalArticles, setTotalArticles] = useState(0);
  const [pageSize] = useState(12);

  // Update user country when location is detected
  useEffect(() => {
    if (location && !locationLoading) {
      setUserCountry(location.countryCode);
    }
  }, [location, locationLoading]);

  // Load featured articles and war streams on mount
  useEffect(() => {
    loadFeaturedArticles();
    loadWarStreams();
  }, []);

  const loadFeaturedArticles = async () => {
    try {
      const featuredData = await unifiedAPI.getFeaturedNews(5);
      setFeaturedArticles(featuredData.featured || []);
    } catch (error) {
      console.error("Failed to load featured articles:", error);
    }
  };

  const loadWarStreams = async () => {
    try {
      const warData = await unifiedAPI.getWarLiveStreams();
      // Convert war_streams to tvChannels format for compatibility
      const warChannels = warData.war_streams || [];
      setWarStreams(warChannels);
    } catch (error) {
      console.error("Failed to load war streams:", error);
    }
  };

  const fetchData = useCallback(async (page: number = currentPage) => {
    setLoading(true);
    setError(null);
    try {
      let data;
      console.log(`[NewsPage] Fetching category: ${activeCategory}, page: ${page}, country: ${userCountry}`);

      if (activeCategory === "tv") {
        const channels = await unifiedAPI.getLiveTVChannels();
        console.log('[NewsPage] TV Channels response:', channels);

        // Combine live channels from YouTube API
        const allChannels = [
          ...(channels.live || []),
          ...(channels.offline || [])
        ];

        setTvChannels(allChannels);
        setArticles([]);
        setTotalPages(1);
        setTotalArticles(0);
      } else if (activeCategory === "headlines") {
        // Use location-based news if country is available
        data = userCountry && !locationLoading
          ? await unifiedAPI.getLocationBasedNews(userCountry, page, pageSize)
          : await unifiedAPI.getNewsHeadlines(page, pageSize, userCountry);

        console.log('[NewsPage] Headlines response:', data);
        const articlesData = data.articles || [];
        setArticles(articlesData.map((a: any, i: number) => ({
          id: a.id || `headline-${page}-${i}`,
          title: a.title,
          summary: a.summary || a.description || "",
          source: a.source || a.publisher || "Unknown",
          published: a.published || a.publishedAt || new Date().toISOString(),
          url: a.url || a.link || "#",
          category: a.category,
          sentiment: a.sentiment || a.ai_sentiment,
          entities: a.entities || a.ai_entities,
          thumbnail_url: a.thumbnail_url,
          image_url: a.image_url,
        })));

        // Set pagination info
        if (data.pagination) {
          setTotalPages(data.pagination.pages);
          setTotalArticles(data.pagination.total);
        }
      } else if (activeCategory === "finance") {
        data = await unifiedAPI.getNewsByCategory("finance", page, pageSize, userCountry);
        console.log('[NewsPage] Finance news response:', data);
        const articlesData = data.articles || [];
        setArticles(articlesData.map((a: any, i: number) => ({
          id: a.id || `finance-${page}-${i}`,
          title: a.title,
          summary: a.summary || a.description || "",
          source: a.source || a.publisher || "Unknown",
          published: a.published || a.publishedAt || new Date().toISOString(),
          url: a.url || a.link || "#",
          category: "finance",
          sentiment: a.sentiment || a.ai_sentiment,
          thumbnail_url: a.thumbnail_url,
          image_url: a.image_url,
        })));

        // Set pagination info
        if (data.pagination) {
          setTotalPages(data.pagination.pages);
          setTotalArticles(data.pagination.total);
        }
      } else {
        data = await unifiedAPI.getNewsByCategory(activeCategory, page, pageSize, userCountry);
        console.log(`[NewsPage] Category ${activeCategory} response:`, data);
        const articlesData = data.articles || [];
        setArticles(articlesData.map((a: any, i: number) => ({
          id: a.id || `${activeCategory}-${page}-${i}`,
          title: a.title,
          summary: a.summary || a.description || "",
          source: a.source || a.publisher || "Unknown",
          published: a.published || a.publishedAt || new Date().toISOString(),
          url: a.url || a.link || "#",
          category: activeCategory,
          sentiment: a.sentiment || a.ai_sentiment,
          thumbnail_url: a.thumbnail_url,
          image_url: a.image_url,
        })));

        // Set pagination info
        if (data.pagination) {
          setTotalPages(data.pagination.pages);
          setTotalArticles(data.pagination.total);
        }
      }

      setLastRefreshed(new Date());

      // Set initial loading to false after first successful load
      if (initialLoading) {
        setInitialLoading(false);
      }

    } catch (err: any) {
      console.error("[NewsPage] Failed to fetch news:", err);
      setError(err.message || "Failed to load news data");
      setInitialLoading(false);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, currentPage, pageSize, userCountry, locationLoading, initialLoading]);

  // Handle page changes
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchData(page);
  };

  // Reset pagination when category changes
  const handleCategoryChange = (category: string) => {
    setActiveCategory(category);
    setCurrentPage(1);
    setTotalPages(1);
    setTotalArticles(0);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await unifiedAPI.searchNews(searchQuery);
      console.log('[NewsPage] Search response:', data);
      const articlesData = data.articles || data.data || [];
      setArticles(articlesData.map((a: any, i: number) => ({
        id: `search-${i}`,
        title: a.title,
        summary: a.summary || a.description || "",
        source: a.source || a.publisher || "Unknown",
        published: a.published || a.publishedAt || new Date().toISOString(),
        url: a.url || a.link || "#",
        category: "search",
        sentiment: a.sentiment,
      })));
    } catch (err: any) {
      console.error("[NewsPage] Search failed:", err);
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(1);
  }, [activeCategory]);

  useEffect(() => {
    fetchData(currentPage);
  }, [currentPage]);

  return (
    <div className="min-h-screen relative" style={{ backgroundColor: DARK_THEME.colors.bgPrimary }}>

      {/* Header Section */}
      <div className="relative z-10 px-4 sm:px-6 lg:px-8 pt-6 pb-4">
        <div className="max-w-7xl mx-auto">
          {/* Title Section - Simplified */}
          <div className="flex items-center gap-4 mb-8">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background: DARK_THEME.colors.gradientPrimary,
              }}
            >
              <Newspaper className="w-6 h-6 text-black" />
            </div>
            <div>
              <h1
                className="text-3xl font-bold tracking-tight text-white"
                style={{ fontFamily: DARK_THEME.font.display }}
              >
                Intelligence Feed
              </h1>
              <p className="text-sm text-zinc-500">
                Aggregated insights from global sources
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex gap-3 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: DARK_THEME.colors.textMuted }} />
              <input
                type="text"
                placeholder="Search news..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="w-full pl-12 pr-4 py-3 rounded-2xl border focus:outline-none transition-all"
                style={{
                  background: DARK_THEME.colors.bgCard,
                  borderColor: DARK_THEME.colors.borderDefault,
                  color: DARK_THEME.colors.textPrimary,
                  fontFamily: DARK_THEME.font.primary,
                  boxShadow: DARK_THEME.shadows.card,
                }}
              />
            </div>
            <DarkButton onClick={handleSearch} icon={Search} size="lg" variant="primary">
              Search
            </DarkButton>
            <DarkButton
              onClick={() => fetchData(currentPage)}
              className="px-4"
              variant="secondary"
              icon={RefreshCw}
            >
              Refresh
            </DarkButton>
          </div>

          {/* Category Tabs */}
          <div className="flex gap-2 flex-wrap mb-4">
            {CATEGORIES.map((cat) => (
              <DarkButton
                key={cat.id}
                active={activeCategory === cat.id}
                onClick={() => handleCategoryChange(cat.id)}
                icon={cat.icon}
                variant={activeCategory === cat.id ? "primary" : "secondary"}
                size="md"
              >
                {cat.label}
              </DarkButton>
            ))}
          </div>

          {/* Results Summary */}
          {activeCategory !== "tv" && totalArticles > 0 && (
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2" style={{ color: DARK_THEME.colors.textMuted }}>
                  <Eye className="w-4 h-4" />
                  <span>{totalArticles} articles</span>
                </div>
                <div className="flex items-center gap-2" style={{ color: DARK_THEME.colors.textMuted }}>
                  <Clock className="w-4 h-4" />
                  <span>Updated {timeAgo(lastRefreshed.toISOString())}</span>
                </div>
              </div>
              {activeCategory === "headlines" && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-lg"
                  style={{ backgroundColor: DARK_THEME.colors.bgActive }}>
                  <Zap className="w-4 h-4" style={{ color: DARK_THEME.colors.primary }} />
                  <span style={{ color: DARK_THEME.colors.primary }}>Live Updates</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="relative z-10 px-4 sm:px-6 lg:px-8 pb-8">
        <div className="max-w-5xl mx-auto">
          {/* Featured Article Section - Simplified */}
          {activeCategory === "headlines" && featuredArticles.length > 0 && !initialLoading && !loading && (
            <div className="mb-10">
              <div className="flex items-center gap-3 mb-4">
                <Sparkles className="w-5 h-5 text-amber-400" />
                <h2 className="text-xl font-bold text-white">Top Feature</h2>
              </div>
              <NewsCard
                article={{
                  ...featuredArticles[0],
                  id: featuredArticles[0].id || "featured-top",
                  published: featuredArticles[0].published || new Date().toISOString(),
                }}
                variant="featured"
              />
            </div>
          )}

          {/* Location Indicator */}
          {location && !locationLoading && userCountry && (
            <div className="mb-8 p-3 rounded-xl border flex items-center gap-3 bg-blue-500/5 border-blue-500/20">
              <MapPin className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-blue-400/80">
                News for {location.country}
              </span>
            </div>
          )}

          {/* Loading State */}
          {initialLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-12 h-12 animate-spin" style={{ color: DARK_THEME.colors.primary }} />
              <p className="mt-4 text-sm font-medium" style={{ color: DARK_THEME.colors.textMuted }}>
                Curating news feed...
              </p>
            </div>
          ) : error && (
            <div className="mb-6 p-4 rounded-xl border flex items-center gap-3 bg-red-500/5 border-red-500/20">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-sm font-medium text-red-400">
                Connection issue: {error}
              </span>
            </div>
          )}

          {!initialLoading && (
            <>
              {loading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-10 h-10 animate-spin opacity-50" style={{ color: DARK_THEME.colors.primary }} />
                </div>
              ) : activeCategory === "tv" ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {tvChannels.map((channel, i) => (
                    <LiveTVChannelEnhanced
                      key={i}
                      channel={{
                        ...channel,
                        id: channel.id || `tv-${i}`,
                        category: channel.category || 'news',
                        is_live: true
                      }}
                    />
                  ))}
                </div>
              ) : articles.length === 0 ? (
                <div className="text-center py-32 opacity-40">
                  <Newspaper className="w-12 h-12 mx-auto mb-4" />
                  <p className="text-lg">No stories matching your criteria</p>
                </div>
              ) : (
                <>
                  {/* News Articles Feed - Single Vertical Column for Simplicity */}
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {articles.map((article) => (
                        <NewsCard
                          key={article.id}
                          article={article}
                          variant="default"
                        />
                      ))}
                    </div>
                  </div>

                  {/* Enhanced Pagination */}
                  {totalPages > 1 && (
                    <div className="mt-16 pt-8 border-t border-white/5">
                      <EnhancedPagination
                        currentPage={currentPage}
                        totalPages={totalPages}
                        onPageChange={handlePageChange}
                        totalItems={totalArticles}
                        itemsPerPage={pageSize}
                      />
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
