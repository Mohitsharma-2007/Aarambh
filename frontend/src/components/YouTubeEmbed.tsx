import React, { useState } from 'react';
import { Tv, ExternalLink, Maximize2, Volume2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface YouTubeEmbedProps {
  videoId: string;
  title: string;
  className?: string;
  autoplay?: boolean;
  muted?: boolean;
}

export function YouTubeEmbed({ 
  videoId, 
  title, 
  className,
  autoplay = false,
  muted = false 
}: YouTubeEmbedProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const embedUrl = `https://www.youtube.com/embed/${videoId}?${new URLSearchParams({
    autoplay: autoplay ? '1' : '0',
    mute: muted ? '1' : '0',
    rel: '0',
    modestbranding: '1',
    fs: isExpanded ? '1' : '0',
    showinfo: '0'
  })}`;

  return (
    <div className={cn("relative bg-black rounded-lg overflow-hidden", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-900 text-white">
        <div className="flex items-center gap-2">
          <Tv className="w-4 h-4" />
          <span className="text-sm font-medium truncate">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
            title={isExpanded ? "Exit fullscreen" : "Fullscreen"}
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <a
            href={`https://www.youtube.com/watch?v=${videoId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:bg-gray-800 rounded transition-colors"
            title="Watch on YouTube"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Video Embed */}
      <div 
        className={cn(
          "relative w-full transition-all duration-300",
          isExpanded ? "aspect-video" : "aspect-video"
        )}
      >
        <iframe
          src={embedUrl}
          title={title}
          className="absolute inset-0 w-full h-full border-0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>

      {/* Controls Overlay */}
      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-1 bg-black/50 text-white px-2 py-1 rounded text-xs">
          <Volume2 className="w-3 h-3" />
          <span>Live</span>
        </div>
        <div className="bg-red-600 text-white px-2 py-1 rounded text-xs font-medium">
          LIVE
        </div>
      </div>
    </div>
  );
}

interface LiveTVChannelProps {
  channel: {
    id: string;
    name: string;
    description?: string;
    thumbnail?: string;
    embed_url?: string;
    stream_key?: string;
    category: string;
    country?: string;
  };
  className?: string;
}

export function LiveTVChannel({ channel, className }: LiveTVChannelProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Extract YouTube video ID from various URL formats
  const extractVideoId = (url: string): string | null => {
    if (!url) return null;
    
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/live\/([^&\n?#]+)/,
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    
    return null;
  };
  
  const videoId = extractVideoId(channel.embed_url || '');
  
  const handleWatchClick = () => {
    if (videoId) {
      setIsPlaying(true);
    } else if (channel.embed_url) {
      window.open(channel.embed_url, '_blank');
    }
  };

  if (isPlaying && videoId) {
    return (
      <YouTubeEmbed
        videoId={videoId}
        title={channel.name}
        className={className}
        autoplay={true}
        muted={true}
      />
    );
  }

  return (
    <div className={cn("bg-white rounded-lg border-2 border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-300", className)}>
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100 cursor-pointer" onClick={handleWatchClick}>
        {channel.thumbnail ? (
          <img 
            src={channel.thumbnail} 
            alt={channel.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Tv className="w-12 h-12 text-gray-400" />
          </div>
        )}
        
        {/* Play Button Overlay */}
        <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
          <div className="bg-red-600 text-white rounded-full p-3">
            <Tv className="w-6 h-6" />
          </div>
        </div>
        
        {/* Live Badge */}
        <div className="absolute top-2 right-2">
          <div className="bg-red-600 text-white px-2 py-1 rounded text-xs font-medium animate-pulse">
            LIVE
          </div>
        </div>
      </div>

      {/* Channel Info */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 mb-1 truncate">{channel.name}</h3>
        {channel.description && (
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{channel.description}</p>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {channel.country && <span>{channel.country}</span>}
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
              {channel.category}
            </span>
          </div>
          
          <button
            onClick={handleWatchClick}
            className="flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
          >
            <Tv className="w-4 h-4" />
            Watch
          </button>
        </div>
      </div>
    </div>
  );
}
