import React from "react";
import {
  ExternalLink,
  Clock,
  Image as ImageIcon,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { cn } from "@/utils/cn";

interface NewsCardProps {
  article: {
    id?: string;
    title: string;
    summary: string;
    source: string;
    url: string;
    category?: string;
    country?: string;
    published: string;
    thumbnail_url?: string;
    image_url?: string;
    sentiment?: { label: string; score: number };
    ai_sentiment?: string;
  };
  className?: string;
  variant?: "default" | "featured" | "compact";
}

export function NewsCard({
  article,
  className,
  variant = "default",
}: NewsCardProps) {
  const timeAgo = (dateStr: string): string => {
    if (!dateStr) return "Recently";
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return `${Math.floor(diff / 60000)}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const getSentimentColor = (label: string): string => {
    switch (label?.toLowerCase()) {
      case "positive":
        return "#34d399";
      case "negative":
        return "#f87171";
      default:
        return "#fbbf24";
    }
  };

  const getSentimentBg = (label: string): string => {
    switch (label?.toLowerCase()) {
      case "positive":
        return "rgba(52,211,153,0.12)";
      case "negative":
        return "rgba(248,113,113,0.12)";
      default:
        return "rgba(251,191,36,0.12)";
    }
  };

  const SentimentIcon = ({ label }: { label: string }) => {
    switch (label?.toLowerCase()) {
      case "positive":
        return <TrendingUp className="w-3 h-3" />;
      case "negative":
        return <TrendingDown className="w-3 h-3" />;
      default:
        return <Minus className="w-3 h-3" />;
    }
  };

  if (variant === "featured") {
    return (
      <div
        className={cn(
          "bg-[#0a0a10]/90 rounded-xl border border-white/[0.07] overflow-hidden hover:border-white/[0.14] transition-all duration-300 group cursor-pointer backdrop-blur-sm relative",
          "shadow-[0_4px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_8px_40px_rgba(0,0,0,0.6)]",
          className,
        )}
      >
        {/* Shiny top edge */}
        <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        {/* Large Featured Image */}
        <div className="aspect-video bg-[#111118] relative overflow-hidden">
          {article.thumbnail_url || article.image_url ? (
            <img
              src={article.thumbnail_url || article.image_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-80 group-hover:opacity-100"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#0d0d14] to-[#111118]">
              <ImageIcon className="w-12 h-12 text-white/10" />
            </div>
          )}
          {/* Image overlay gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a10] via-transparent to-transparent opacity-60" />

          {/* Source badge */}
          <div className="absolute top-3 left-3">
            <span className="bg-black/70 backdrop-blur-md text-white/70 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-white/10">
              {article.source}
            </span>
          </div>

          {/* Sentiment badge */}
          {(article.sentiment?.label || article.ai_sentiment) && (
            <div className="absolute top-3 right-3">
              <span
                className="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center gap-1.5 backdrop-blur-md border"
                style={{
                  color: getSentimentColor(
                    article.sentiment?.label || article.ai_sentiment || "",
                  ),
                  backgroundColor: getSentimentBg(
                    article.sentiment?.label || article.ai_sentiment || "",
                  ),
                  borderColor: `${getSentimentColor(article.sentiment?.label || article.ai_sentiment || "")}30`,
                }}
              >
                <SentimentIcon
                  label={article.sentiment?.label || article.ai_sentiment || ""}
                />
                {article.sentiment?.label || article.ai_sentiment}
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-5">
          <h3 className="text-base font-bold text-white/80 group-hover:text-white mb-2 line-clamp-2 leading-snug transition-colors">
            {article.title}
          </h3>

          {article.summary && (
            <p className="text-[11px] text-white/30 mb-4 line-clamp-2 leading-relaxed">
              {article.summary}
            </p>
          )}

          <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
            <div className="flex items-center gap-2 text-[10px] text-white/25">
              <Clock className="w-3 h-3" />
              <span>{timeAgo(article.published)}</span>
            </div>

            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-[10px] font-bold text-violet-400/70 hover:text-violet-400 transition-colors uppercase tracking-wider"
              onClick={(e) => e.stopPropagation()}
            >
              Read <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    );
  }

  if (variant === "compact") {
    return (
      <div
        className={cn(
          "bg-[#0a0a10]/80 rounded-lg border border-white/[0.06] p-3 hover:border-white/[0.12] hover:bg-[#0d0d15]/90 transition-all duration-200 group cursor-pointer",
          className,
        )}
      >
        <div className="flex gap-3">
          {/* Thumbnail */}
          <div className="flex-shrink-0 w-20 h-20 bg-[#111118] rounded-lg overflow-hidden border border-white/[0.05]">
            {article.thumbnail_url || article.image_url ? (
              <img
                src={article.thumbnail_url || article.image_url}
                alt={article.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 opacity-75 group-hover:opacity-100"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <ImageIcon className="w-6 h-6 text-white/10" />
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-white/70 group-hover:text-white/90 text-[12px] mb-1 line-clamp-2 leading-snug transition-colors">
              {article.title}
            </h4>

            <div className="flex items-center justify-between mt-2">
              <span className="text-[10px] text-white/30 font-bold uppercase tracking-wider">
                {article.source}
              </span>
              <span className="text-[10px] text-white/20">
                {timeAgo(article.published)}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div
      className={cn(
        "bg-[#0a0a10]/80 rounded-xl border border-white/[0.07] overflow-hidden hover:border-white/[0.13] hover:bg-[#0d0d15]/90 transition-all duration-300 group cursor-pointer relative",
        "shadow-[0_2px_16px_rgba(0,0,0,0.3)] hover:shadow-[0_4px_30px_rgba(0,0,0,0.5)]",
        className,
      )}
    >
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/8 to-transparent" />
      <div className="flex">
        {/* Thumbnail */}
        <div className="flex-shrink-0 w-32 h-32 bg-[#111118] relative border-r border-white/[0.05]">
          {article.thumbnail_url || article.image_url ? (
            <img
              src={article.thumbnail_url || article.image_url}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-70 group-hover:opacity-90"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#0d0d14] to-[#111118]">
              <ImageIcon className="w-8 h-8 text-white/8" />
            </div>
          )}
          {/* gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-[#0a0a10]/30" />
        </div>

        {/* Content */}
        <div className="flex-1 p-4">
          {/* Source and sentiment */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold text-white/25 uppercase tracking-widest">
              {article.source}
            </span>

            {(article.sentiment?.label || article.ai_sentiment) && (
              <span
                className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider flex items-center gap-1 border"
                style={{
                  color: getSentimentColor(
                    article.sentiment?.label || article.ai_sentiment || "",
                  ),
                  backgroundColor: getSentimentBg(
                    article.sentiment?.label || article.ai_sentiment || "",
                  ),
                  borderColor: `${getSentimentColor(article.sentiment?.label || article.ai_sentiment || "")}25`,
                }}
              >
                <SentimentIcon
                  label={article.sentiment?.label || article.ai_sentiment || ""}
                />
                {article.sentiment?.label || article.ai_sentiment}
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="font-bold text-white/75 group-hover:text-white mb-2 line-clamp-2 leading-snug text-sm transition-colors">
            {article.title}
          </h3>

          {/* Summary */}
          {article.summary && (
            <p className="text-[11px] text-white/25 mb-3 line-clamp-1 leading-relaxed">
              {article.summary}
            </p>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-2 border-t border-white/[0.05]">
            <div className="flex items-center gap-1.5 text-[10px] text-white/20">
              <Clock className="w-3 h-3" />
              <span>{timeAgo(article.published)}</span>
            </div>

            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-[10px] font-bold text-violet-400/60 hover:text-violet-400 transition-colors uppercase tracking-wider"
              onClick={(e) => e.stopPropagation()}
            >
              Read <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
