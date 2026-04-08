import { useState, useRef } from "react";
import { cn } from "@/utils/cn";
import {
  Globe,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

const TOKENS = {
  colors: {
    bg: "#07080C",
    geo: "#0EA5E9",
    border: "rgba(255, 255, 255, 0.08)",
    textPrimary: "#FFFFFF",
    textMuted: "rgba(255, 255, 255, 0.4)",
  },
};

export default function GlobePage() {
  const [iframeError, setIframeError] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const iframeUrl = "https://liveuamap.com/";

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#07080C]">
      <div className="w-full h-full relative">
        {!iframeError ? (
          <iframe
            ref={iframeRef}
            src={iframeUrl}
            className="w-full h-full border-0"
            title="Global Intelligence — Live Map"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
            onError={() => setIframeError(true)}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8 bg-[#07080C]">
            <Globe className="w-16 h-16" style={{ color: TOKENS.colors.border }} />
            <p className="text-base font-bold text-white">Map blocked by browser security</p>
            <p className="text-sm text-white/40">
              LiveUAMap may not allow iframe embedding in this browser.
            </p>
            <a
              href={iframeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-6 py-3 rounded-xl text-white text-sm font-bold"
              style={{ backgroundColor: TOKENS.colors.geo }}
            >
              <ExternalLink className="w-4 h-4" />
              Open in New Tab
            </a>
            <button
              onClick={() => { setIframeError(false); }}
              className="mt-2 flex items-center gap-1.5 text-xs text-white/60 hover:text-white transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Retry Loader
            </button>
          </div>
        )}

        {/* Floating Refresh Button - OPTIONAL/Minimal UI */}
        <button
          onClick={() => { if (iframeRef.current) iframeRef.current.src = iframeUrl; }}
          className="absolute bottom-6 right-6 p-3 rounded-full bg-white/5 backdrop-blur-md border border-white/10 text-white/40 hover:text-white hover:bg-white/10 transition-all z-50 shadow-2xl"
          title="Refresh Map"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
