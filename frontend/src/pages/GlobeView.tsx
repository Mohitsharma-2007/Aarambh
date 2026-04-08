import { useEffect, useState, useCallback, useRef } from "react";
import axios from "axios";
import {
  MapPin,
  AlertTriangle,
  Globe,
  RefreshCw,
  ExternalLink,
  Activity,
  Zap,
  Shield,
  Info,
  Newspaper,
  Search,
} from "lucide-react";
import { cn } from "@/utils/cn";

const SERP_API = "http://localhost:8003";

// ── Types ──────────────────────────────────────────────────────────────────────

interface Region {
  label: string;
  url: string;
  lat: number;
  lng: number;
  zoom: number;
}

interface ACLEDEvent {
  event_id_cnty?: string;
  event_date?: string;
  event_type?: string;
  sub_event_type?: string;
  actor1?: string;
  actor2?: string;
  country?: string;
  location?: string;
  latitude?: number | string;
  longitude?: number | string;
  fatalities?: number | string;
  notes?: string;
  source?: string;
  iso?: string;
}

interface NewsItem {
  title?: string;
  link?: string;
  source?: string;
  snippet?: string;
  date?: string;
  thumbnail?: string;
}

// ── Event type colors ──────────────────────────────────────────────────────────

function eventColor(type: string = ""): string {
  const t = type.toLowerCase();
  if (t.includes("battle") || t.includes("armed"))
    return "text-red-400 bg-red-400/10 border-red-400/30";
  if (t.includes("violence") || t.includes("civilian"))
    return "text-orange-400 bg-orange-400/10 border-orange-400/30";
  if (t.includes("protest") || t.includes("riot"))
    return "text-yellow-400 bg-yellow-400/10 border-yellow-400/30";
  if (t.includes("explosion") || t.includes("remote"))
    return "text-red-500 bg-red-500/10 border-red-500/30";
  return "text-gray-400 bg-gray-400/10 border-gray-400/30";
}

function eventIcon(type: string = "") {
  const t = type.toLowerCase();
  if (t.includes("battle") || t.includes("armed")) return "⚔️";
  if (t.includes("violence")) return "💔";
  if (t.includes("protest")) return "✊";
  if (t.includes("riot")) return "🔥";
  if (t.includes("explosion")) return "💥";
  return "📍";
}

function timeAgo(d: string | undefined): string {
  if (!d) return "";
  try {
    const ms = Date.now() - new Date(d).getTime();
    const days = Math.floor(ms / 86400000);
    if (days === 0) return "Today";
    if (days === 1) return "Yesterday";
    return `${days}d ago`;
  } catch {
    return d;
  }
}

// ── Skeleton ───────────────────────────────────────────────────────────────────

function Sk({ className = "" }: { className?: string }) {
  return (
    <div className={cn("animate-pulse rounded bg-gray-700/50", className)} />
  );
}

// ── Main Component ──────────────────────────────────────────────────────────────

export default function GlobeView() {
  const [regions, setRegions] = useState<Record<string, Region>>({});
  const [selectedRegion, setSelectedRegion] = useState("world");
  const [acledEvents, setAcledEvents] = useState<ACLEDEvent[]>([]);
  const [acledStatus, setAcledStatus] = useState<
    "loading" | "ok" | "unconfigured" | "error"
  >("loading");
  const [regionNews, setRegionNews] = useState<NewsItem[]>([]);
  const [tensions, setTensions] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [iframeError, setIframeError] = useState(false);
  const [activePanel, setActivePanel] = useState<"events" | "news" | "info">(
    "events",
  );
  const [searchCountry, setSearchCountry] = useState("");
  const [regionGroup, setRegionGroup] = useState<"conflict" | "global" | "all">(
    "conflict",
  );
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Fetch regions list
  useEffect(() => {
    axios
      .get(`${SERP_API}/api/globe/regions`, { timeout: 10000 })
      .then((r) => setRegions(r.data.regions || {}))
      .catch(() => {});
  }, []);

  // Fetch ACLED + news when region changes
  const loadRegionData = useCallback(
    async (regionKey: string) => {
      const reg = regions[regionKey];
      if (!reg) return;
      setAcledStatus("loading");
      setAcledEvents([]);
      setRegionNews([]);

      // Extract country name from region label (strip emoji)
      const countryName = reg.label
        .replace(/[^\w\s/]/g, "")
        .trim()
        .replace("  ", " ");

      const [acledRes, newsRes] = await Promise.all([
        axios
          .get(`${SERP_API}/api/globe/acled`, {
            params: {
              country: countryName !== "World" ? countryName : "",
              limit: 50,
            },
            timeout: 15000,
          })
          .catch(() => null),
        axios
          .get(`${SERP_API}/api/globe/news/${regionKey}`, { timeout: 15000 })
          .catch(() => null),
      ]);

      // ACLED
      if (acledRes?.data?.status === "unconfigured") {
        setAcledStatus("unconfigured");
      } else if (acledRes?.data?.events) {
        setAcledEvents(acledRes.data.events);
        setAcledStatus("ok");
      } else {
        setAcledStatus("error");
      }

      // News
      setRegionNews(newsRes?.data?.articles || []);
      setLoading(false);
    },
    [regions],
  );

  useEffect(() => {
    if (Object.keys(regions).length > 0) {
      loadRegionData(selectedRegion);
    }
  }, [selectedRegion, regions, loadRegionData]);

  // Load tensions data once
  useEffect(() => {
    axios
      .get(`${SERP_API}/api/globe/tensions`, { timeout: 15000 })
      .then((r) => setTensions(r.data))
      .catch(() => {});
  }, []);

  const currentRegion = regions[selectedRegion];
  const iframeUrl = currentRegion?.url || "https://liveuamap.com/";

  // Filter regions
  const CONFLICT_KEYS = [
    "ukraine",
    "iran",
    "israel-palestine",
    "syria",
    "lebanon",
    "yemen",
    "sudan",
    "myanmar",
    "afghanistan",
    "caucasus",
    "kashmir",
    "middleeast",
  ];
  const GLOBAL_KEYS = [
    "world",
    "europe",
    "africa",
    "russia",
    "korea",
    "taiwan",
  ];

  const filteredRegionKeys = Object.keys(regions)
    .filter((k) => {
      if (regionGroup === "conflict") return CONFLICT_KEYS.includes(k);
      if (regionGroup === "global") return GLOBAL_KEYS.includes(k);
      return true;
    })
    .filter((k) => {
      if (!searchCountry) return true;
      return regions[k]?.label
        ?.toLowerCase()
        .includes(searchCountry.toLowerCase());
    });

  const fatalityTotal = acledEvents.reduce(
    (sum, e) => sum + (parseInt(String(e.fatalities || 0)) || 0),
    0,
  );
  const eventTypes = [
    ...new Set(acledEvents.map((e) => e.event_type).filter(Boolean)),
  ];

  return (
    <div className="h-[calc(100vh-48px)] flex bg-[#0a0a0a] text-gray-100 overflow-hidden">
      {/* ── LEFT PANEL — Region Selector ─────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 flex flex-col border-r border-gray-800 bg-[#111] overflow-hidden">
        {/* Header */}
        <div className="px-3 py-3 border-b border-gray-800">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-4 h-4 text-red-400" />
            <span className="text-sm font-semibold text-gray-100">
              Conflict Map
            </span>
          </div>
          {/* Search */}
          <div className="flex items-center bg-gray-800/60 border border-gray-700/40 rounded-lg px-2.5 py-1.5">
            <Search className="w-3 h-3 text-gray-500 flex-shrink-0" />
            <input
              value={searchCountry}
              onChange={(e) => setSearchCountry(e.target.value)}
              placeholder="Filter regions..."
              className="flex-1 bg-transparent px-2 text-xs text-gray-300 placeholder-gray-600 outline-none"
            />
          </div>
        </div>

        {/* Group tabs */}
        <div className="flex border-b border-gray-800">
          {(["conflict", "global", "all"] as const).map((g) => (
            <button
              key={g}
              onClick={() => setRegionGroup(g)}
              className={cn(
                "flex-1 py-1.5 text-[10px] font-medium capitalize transition-colors",
                regionGroup === g
                  ? "text-blue-400 bg-blue-500/10"
                  : "text-gray-500 hover:text-gray-300",
              )}
            >
              {g}
            </button>
          ))}
        </div>

        {/* Region List */}
        <div className="flex-1 overflow-y-auto">
          {filteredRegionKeys.map((key) => {
            const r = regions[key];
            const isSelected = key === selectedRegion;
            return (
              <button
                key={key}
                onClick={() => {
                  setSelectedRegion(key);
                  setIframeError(false);
                }}
                className={cn(
                  "w-full flex items-center gap-2.5 px-3 py-2.5 text-left transition-all border-l-2",
                  isSelected
                    ? "bg-blue-500/10 border-l-blue-500 text-white"
                    : "border-l-transparent text-gray-400 hover:bg-gray-800/40 hover:text-gray-200",
                )}
              >
                <span className="text-base flex-shrink-0 w-6 text-center">
                  {r.label.match(
                    /[\u{1F1E0}-\u{1F1FF}]{2}|[\u{1F300}-\u{1FFFF}]/u,
                  )?.[0] || "🌍"}
                </span>
                <span className="text-xs font-medium truncate">
                  {r.label.replace(/[^\w\s/]/g, "").trim()}
                </span>
                {isSelected && (
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 ml-auto flex-shrink-0" />
                )}
              </button>
            );
          })}
        </div>

        {/* Attribution */}
        <div className="px-3 py-2 border-t border-gray-800 bg-gray-900/50">
          <p className="text-[10px] text-gray-600">Data sources:</p>
          <div className="flex flex-col gap-0.5 mt-0.5">
            <a
              href="https://liveuamap.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-blue-500/70 hover:text-blue-400 flex items-center gap-1"
            >
              liveuamap.com <ExternalLink className="w-2.5 h-2.5" />
            </a>
            <a
              href="https://acleddata.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-blue-500/70 hover:text-blue-400 flex items-center gap-1"
            >
              acleddata.com <ExternalLink className="w-2.5 h-2.5" />
            </a>
            <a
              href="https://worldtensionwatch.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-blue-500/70 hover:text-blue-400 flex items-center gap-1"
            >
              worldtensionwatch.com <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>
        </div>
      </aside>

      {/* ── CENTER — LiveUAMap iframe ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Map header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-[#111] flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
            <span className="text-sm font-semibold text-gray-100">
              {currentRegion?.label?.replace(/[^\w\s/]/g, "").trim() || "World"}{" "}
              — Live Map
            </span>
            <span className="text-xs text-gray-500">
              powered by liveuamap.com
            </span>
          </div>
          <div className="flex items-center gap-2">
            <a
              href={iframeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1 text-xs bg-blue-500/20 border border-blue-500/30 text-blue-400 rounded-full hover:bg-blue-500/30 transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              Open full map
            </a>
            <button
              onClick={() => {
                setIframeError(false);
                if (iframeRef.current) iframeRef.current.src = iframeUrl;
              }}
              className="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-gray-200"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* iframe */}
        <div className="flex-1 relative bg-gray-900">
          {!iframeError ? (
            <iframe
              ref={iframeRef}
              key={iframeUrl}
              src={iframeUrl}
              className="w-full h-full border-0"
              title={`LiveUAMap — ${selectedRegion}`}
              sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-top-navigation"
              referrerPolicy="no-referrer-when-downgrade"
              onError={() => setIframeError(true)}
              loading="lazy"
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
              <Globe className="w-16 h-16 text-gray-700" />
              <div>
                <p className="text-base font-medium text-gray-300">
                  Map blocked by browser security policy
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  LiveUAMap may not allow iframe embedding in this browser.
                </p>
                <p className="text-xs text-gray-600 mt-2">
                  This is a browser-level restriction (X-Frame-Options / CSP).
                </p>
              </div>
              <a
                href={iframeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 bg-blue-500/20 border border-blue-500/40 text-blue-400 rounded-xl hover:bg-blue-500/30 transition-colors text-sm font-medium"
              >
                <ExternalLink className="w-4 h-4" />
                Open{" "}
                {currentRegion?.label?.replace(/[^\w\s/]/g, "").trim() ||
                  "World"}{" "}
                Map in New Tab
              </a>
              <p className="text-xs text-gray-600">
                The ACLED conflict events panel on the right still works.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT PANEL — ACLED + News + Info ────────────────────────── */}
      <aside className="w-80 flex-shrink-0 flex flex-col border-l border-gray-800 bg-[#111] overflow-hidden">
        {/* Panel tabs */}
        <div className="flex border-b border-gray-800">
          {(["events", "news", "info"] as const).map((p) => (
            <button
              key={p}
              onClick={() => setActivePanel(p)}
              className={cn(
                "flex-1 py-2.5 text-xs font-medium capitalize transition-colors border-b-2",
                activePanel === p
                  ? "text-blue-400 border-blue-500 bg-blue-500/5"
                  : "text-gray-500 border-transparent hover:text-gray-300",
              )}
            >
              {p === "events"
                ? "⚔️ Events"
                : p === "news"
                  ? "📰 News"
                  : "ℹ️ Info"}
            </button>
          ))}
        </div>

        {/* Stats bar */}
        {activePanel === "events" && (
          <div className="px-3 py-2 bg-gray-900/50 border-b border-gray-800 flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-blue-400" />
              <span className="text-xs text-gray-400">
                {acledEvents.length} events
              </span>
            </div>
            {fatalityTotal > 0 && (
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3 text-red-400" />
                <span className="text-xs text-red-400">
                  {fatalityTotal} fatalities
                </span>
              </div>
            )}
            <span className="text-[10px] text-gray-600 ml-auto">
              Last 30 days
            </span>
          </div>
        )}

        {/* Panel content */}
        <div className="flex-1 overflow-y-auto">
          {/* ── Events Panel ── */}
          {activePanel === "events" && (
            <>
              {acledStatus === "unconfigured" ? (
                <div className="p-4 text-center">
                  <Shield className="w-8 h-8 text-yellow-500/40 mx-auto mb-3" />
                  <h3 className="text-sm font-semibold text-yellow-400 mb-2">
                    ACLED API Not Configured
                  </h3>
                  <p className="text-xs text-gray-400 leading-relaxed mb-3">
                    Register for a free API key to access real conflict event
                    data from ACLED (Armed Conflict Location &amp; Event Data
                    Project).
                  </p>
                  <a
                    href="https://developer.acleddata.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-yellow-500/20 border border-yellow-500/30 text-yellow-400 rounded-lg text-xs hover:bg-yellow-500/30 transition-colors"
                  >
                    Get Free API Key <ExternalLink className="w-3 h-3" />
                  </a>
                  <p className="text-[10px] text-gray-600 mt-3">
                    After registering, add{" "}
                    <code className="text-blue-400">ACLED_API_KEY</code> and{" "}
                    <code className="text-blue-400">ACLED_EMAIL</code> to{" "}
                    <code className="text-gray-400">serpapi_service/.env</code>
                  </p>
                </div>
              ) : acledStatus === "loading" ? (
                <div className="p-3 space-y-2">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className="p-2 rounded border border-gray-700/30"
                    >
                      <Sk className="h-3 w-3/4 mb-1.5" />
                      <Sk className="h-2 w-1/2" />
                    </div>
                  ))}
                </div>
              ) : acledEvents.length === 0 ? (
                <div className="p-4 text-center">
                  <Info className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    No events found for this region
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    Try a different region or check ACLED configuration
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-800/50">
                  {acledEvents.map((evt, i) => (
                    <div
                      key={evt.event_id_cnty || i}
                      className="p-3 hover:bg-gray-800/30 transition-colors"
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-base flex-shrink-0">
                          {eventIcon(evt.event_type)}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap mb-1">
                            <span
                              className={cn(
                                "text-[10px] font-medium px-1.5 py-0.5 rounded border",
                                eventColor(evt.event_type),
                              )}
                            >
                              {evt.sub_event_type ||
                                evt.event_type ||
                                "Unknown"}
                            </span>
                            {evt.fatalities &&
                              parseInt(String(evt.fatalities)) > 0 && (
                                <span className="text-[10px] text-red-400">
                                  💀 {evt.fatalities}
                                </span>
                              )}
                          </div>
                          {(evt.actor1 || evt.actor2) && (
                            <p className="text-xs font-medium text-gray-300 truncate mb-0.5">
                              {[evt.actor1, evt.actor2]
                                .filter(Boolean)
                                .join(" vs ")}
                            </p>
                          )}
                          <p className="text-xs text-gray-500 flex items-center gap-1">
                            <MapPin className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">
                              {evt.location || evt.country}
                            </span>
                            <span className="flex-shrink-0 ml-auto">
                              {timeAgo(evt.event_date)}
                            </span>
                          </p>
                          {evt.notes && (
                            <p className="text-[10px] text-gray-600 mt-1 line-clamp-2">
                              {evt.notes}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── News Panel ── */}
          {activePanel === "news" && (
            <div className="divide-y divide-gray-800/40">
              {regionNews.length === 0 ? (
                <div className="p-4 text-center">
                  <Newspaper className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    Loading conflict news...
                  </p>
                </div>
              ) : (
                regionNews.map((item, i) => (
                  <a
                    key={item.link || `news-${i}`}
                    href={item.link || "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2 p-3 hover:bg-gray-800/30 group transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-300 line-clamp-2 group-hover:text-blue-300 transition-colors leading-snug">
                        {item.title}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1">
                        {item.source && (
                          <span className="text-[10px] text-blue-400/70">
                            {item.source}
                          </span>
                        )}
                        {item.date && (
                          <span className="text-[10px] text-gray-600">
                            · {item.date}
                          </span>
                        )}
                      </div>
                      {item.snippet && (
                        <p className="text-[10px] text-gray-600 mt-1 line-clamp-2">
                          {item.snippet}
                        </p>
                      )}
                    </div>
                    {item.thumbnail && (
                      <img
                        src={item.thumbnail}
                        alt=""
                        className="w-14 h-10 object-cover rounded flex-shrink-0"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    )}
                  </a>
                ))
              )}
            </div>
          )}

          {/* ── Info Panel ── */}
          {activePanel === "info" && (
            <div className="p-4 space-y-4">
              {/* Region Info */}
              {currentRegion && (
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                  <h3 className="text-sm font-semibold text-gray-100 mb-2">
                    {currentRegion.label}
                  </h3>
                  <div className="space-y-1.5 text-xs text-gray-400">
                    <p>
                      📍 Coordinates: {currentRegion.lat.toFixed(1)},{" "}
                      {currentRegion.lng.toFixed(1)}
                    </p>
                    <p>🔍 Zoom level: {currentRegion.zoom}</p>
                    <a
                      href={currentRegion.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
                    >
                      🗺️ Open on LiveUAMap <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              )}

              {/* WorldTensionWatch Info */}
              {tensions && (
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <h3 className="text-sm font-semibold text-gray-100">
                      WorldTensionWatch
                    </h3>
                  </div>
                  {tensions.status === "error" ? (
                    <p className="text-xs text-gray-500">
                      Could not fetch tension data
                    </p>
                  ) : (
                    <div className="space-y-1.5">
                      {tensions.site_info?.title && (
                        <p className="text-xs text-gray-300">
                          {tensions.site_info.title}
                        </p>
                      )}
                      {tensions.site_info?.description && (
                        <p className="text-xs text-gray-500">
                          {tensions.site_info.description}
                        </p>
                      )}
                      {tensions.site_info?.headings?.length > 0 && (
                        <div className="mt-2">
                          {tensions.site_info.headings
                            .slice(0, 4)
                            .map((h: string, i: number) => (
                              <p
                                key={i}
                                className="text-xs text-gray-400 py-0.5 border-b border-gray-700/30"
                              >
                                • {h}
                              </p>
                            ))}
                        </div>
                      )}
                      <a
                        href="https://worldtensionwatch.com/global"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-2"
                      >
                        View on WorldTensionWatch{" "}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  )}
                </div>
              )}

              {/* ACLED Summary */}
              {acledStatus === "ok" && acledEvents.length > 0 && (
                <div className="bg-gray-800/30 rounded-xl p-4 border border-gray-700/30">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-4 h-4 text-red-400" />
                    <h3 className="text-sm font-semibold text-gray-100">
                      ACLED Summary
                    </h3>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Total events (30d)</span>
                      <span className="text-gray-200 font-medium">
                        {acledEvents.length}
                      </span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-400">Total fatalities</span>
                      <span className="text-red-400 font-medium">
                        {fatalityTotal}
                      </span>
                    </div>
                    {eventTypes.slice(0, 4).map((type) => {
                      const count = acledEvents.filter(
                        (e) => e.event_type === type,
                      ).length;
                      const pct = Math.round(
                        (count / acledEvents.length) * 100,
                      );
                      return (
                        <div key={type} className="space-y-0.5">
                          <div className="flex justify-between text-[10px]">
                            <span className="text-gray-500">{type}</span>
                            <span className="text-gray-400">
                              {count} ({pct}%)
                            </span>
                          </div>
                          <div className="h-1 bg-gray-700 rounded overflow-hidden">
                            <div
                              className="h-full bg-red-500/60 rounded"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Data Sources */}
              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Data Sources
                </h3>
                {[
                  {
                    name: "LiveUAMap",
                    url: "https://liveuamap.com",
                    desc: "Real-time conflict map feed",
                  },
                  {
                    name: "ACLED",
                    url: "https://acleddata.com",
                    desc: "Armed Conflict Location & Event Data",
                  },
                  {
                    name: "WorldTensionWatch",
                    url: "https://worldtensionwatch.com",
                    desc: "AI-processed global tensions",
                  },
                ].map((s) => (
                  <a
                    key={s.name}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start gap-2 p-2.5 bg-gray-800/30 border border-gray-700/30 rounded-lg hover:bg-gray-800/50 transition-colors group"
                  >
                    <div className="flex-1">
                      <p className="text-xs font-medium text-blue-400 group-hover:text-blue-300">
                        {s.name}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-0.5">
                        {s.desc}
                      </p>
                    </div>
                    <ExternalLink className="w-3 h-3 text-gray-600 flex-shrink-0 mt-0.5" />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
