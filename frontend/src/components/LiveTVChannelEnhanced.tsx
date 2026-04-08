import React, { useState } from 'react';
import { Tv, ExternalLink, Maximize2, Volume2, Users, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

interface LiveTVChannelEnhancedProps {
  channel: {
    id: string;
    name: string;
    description?: string;
    thumbnail?: string;
    embed_url?: string;
    stream_url?: string;
    video_id?: string;
    channel_id?: string;
    category: string;
    country?: string;
    is_live?: boolean;
    title?: string;
    live_viewers?: number;
    started_at?: string;
  };
  className?: string;
  showLiveStatus?: boolean;
}

export function LiveTVChannelEnhanced({ 
  channel, 
  className,
  showLiveStatus = true 
}: LiveTVChannelEnhancedProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleWatchClick = async () => {
    if (!channel.is_live && !channel.embed_url) {
      return; // Don't try to play offline channels
    }
    
    setIsLoading(true);
    // Simulate loading delay
    setTimeout(() => {
      setIsPlaying(true);
      setIsLoading(false);
    }, 500);
  };

  const formatViewers = (viewers: number = 0): string => {
    if (viewers >= 1000000) {
      return `${(viewers / 1000000).toFixed(1)}M`;
    } else if (viewers >= 1000) {
      return `${(viewers / 1000).toFixed(1)}K`;
    }
    return viewers.toString();
  };

  const getLiveStatusColor = () => {
    if (channel.is_live) return "bg-red-600";
    return "bg-gray-500";
  };

  const getLiveStatusText = () => {
    if (channel.is_live) return "LIVE";
    return "OFFLINE";
  };

  if (isPlaying && channel.embed_url) {
    return (
      <div className={cn("relative bg-black rounded-lg overflow-hidden", className)}>
        {/* Header */}
        <div className="flex items-center justify-between p-3 bg-gray-900 text-white">
          <div className="flex items-center gap-2">
            <Tv className="w-4 h-4" />
            <span className="text-sm font-medium truncate">{channel.name}</span>
            <span className="px-2 py-1 bg-red-600 rounded text-xs font-medium animate-pulse">
              LIVE
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(false)}
              className="p-1 hover:bg-gray-800 rounded transition-colors"
              title="Close stream"
            >
              ✕
            </button>
            <button
              onClick={() => window.open(channel.stream_url, '_blank')}
              className="p-1 hover:bg-gray-800 rounded transition-colors"
              title="Watch on YouTube"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Video Embed */}
        <div className="relative w-full aspect-video">
          <iframe
            src={channel.embed_url}
            title={channel.name}
            className="absolute inset-0 w-full h-full border-0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>

        {/* Live Stats Overlay */}
        {channel.live_viewers && (
          <div className="absolute bottom-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
            <Users className="w-3 h-3" />
            <span>{formatViewers(channel.live_viewers)} watching</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={cn(
      "bg-white rounded-xl border-2 overflow-hidden transition-all duration-300",
      channel.is_live ? "border-red-200 shadow-lg" : "border-gray-200",
      className
    )}>
      {/* Thumbnail */}
      <div 
        className={cn(
          "relative aspect-video bg-gray-100 cursor-pointer overflow-hidden",
          !channel.is_live && "opacity-75"
        )}
        onClick={handleWatchClick}
      >
        {channel.thumbnail ? (
          <img 
            src={channel.thumbnail} 
            alt={channel.name}
            className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
            <Tv className="w-12 h-12 text-gray-400" />
          </div>
        )}
        
        {/* Live Status Badge */}
        <div className="absolute top-2 left-2">
          <div className={cn(
            "px-2 py-1 rounded text-xs font-medium text-white flex items-center gap-1",
            getLiveStatusColor()
          )}>
            {channel.is_live ? (
              <>
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                {getLiveStatusText()}
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3" />
                {getLiveStatusText()}
              </>
            )}
          </div>
        </div>

        {/* Viewers Count */}
        {channel.is_live && channel.live_viewers && (
          <div className="absolute top-2 right-2">
            <div className="bg-black/70 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
              <Users className="w-3 h-3" />
              <span>{formatViewers(channel.live_viewers)}</span>
            </div>
          </div>
        )}

        {/* Play Button Overlay */}
        {channel.is_live && (
          <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
            <div className="bg-red-600 text-white rounded-full p-4 transform hover:scale-110 transition-transform">
              {isLoading ? (
                <div className="w-6 h-6 border-2 border-white border-t-transparent animate-spin" />
              ) : (
                <Tv className="w-6 h-6" />
              )}
            </div>
          </div>
        )}

        {/* Category Badge */}
        <div className="absolute bottom-2 right-2">
          <span className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-medium">
            {channel.category}
          </span>
        </div>
      </div>

      {/* Channel Info */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-bold text-gray-900 mb-1">{channel.name}</h3>
            {channel.title && channel.is_live && (
              <p className="text-sm text-gray-600 line-clamp-2">{channel.title}</p>
            )}
          </div>
          {channel.is_live && (
            <CheckCircle className="w-5 h-5 text-red-600 flex-shrink-0 ml-2" />
          )}
        </div>
        
        {channel.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{channel.description}</p>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {channel.country && <span>{channel.country}</span>}
            {channel.started_at && channel.is_live && (
              <span>Started {new Date(channel.started_at).toLocaleTimeString()}</span>
            )}
          </div>
          
          {channel.is_live ? (
            <button
              onClick={handleWatchClick}
              className="flex items-center gap-1 text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-red-600 border-t-transparent animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <Tv className="w-4 h-4" />
                  Watch Live
                </>
              )}
            </button>
          ) : (
            <div className="text-sm text-gray-500 italic">
              Channel Offline
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
