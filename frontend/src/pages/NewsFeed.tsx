import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import {
  Search,
  RefreshCw,
  Clock,
  ExternalLink,
  Newspaper,
  TrendingUp,
  Menu,
  Bell,
  Settings,
  MoreVertical,
  ChevronRight,
  Globe,
  Star,
  MapPin,
  Briefcase,
  Cpu,
  Tv,
  Trophy,
  FlaskConical,
  HeartPulse,
  LayoutGrid,
  PlusCircle,
  Bookmark,
  Share2,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { NewsAPI } from "@/api/client";

const SERP_API = "http://localhost:8003";

interface NewsItem {
  id: string;
  title: string;
  excerpt: string;
  source: string;
  time: string;
  thumbnail?: string;
  category: string;
  link?: string;
}

const SIDEBAR_ITEMS = [
  { id: "Home", icon: Newspaper, label: "Home" },
  { id: "For you", icon: Star, label: "For you" },
  { id: "Following", icon: Bookmark, label: "Following" },
  { id: "News Showcase", icon: LayoutGrid, label: "News Showcase" },
];

const TOPICS = [
  { id: "India", icon: MapPin, label: "India" },
  { id: "World", icon: Globe, label: "World" },
  { id: "Local", icon: MapPin, label: "Local" },
  { id: "Business", icon: Briefcase, label: "Business" },
  { id: "Technology", icon: Cpu, label: "Technology" },
  { id: "Entertainment", icon: Tv, label: "Entertainment" },
  { id: "Sports", icon: Trophy, label: "Sports" },
  { id: "Science", icon: FlaskConical, label: "Science" },
  { id: "Health", icon: HeartPulse, label: "Health" },
];

function timeAgo(dateStr: string): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return `${Math.floor(diff / 60000)}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function NewsFeed() {
  const [activeCategory, setActiveCategory] = useState("Home");
  const [articles, setArticles] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [provider, setProvider] = useState<"serp" | "voralis">("voralis");
  const [lastRefreshed, setLastRefreshed] = useState(new Date());

  const fetchData = useCallback(async () => {
    setLoading(true);
    let success = false;
    let data_to_set: NewsItem[] = [];

    const tryVoralis = async () => {
      try {
        const data = await NewsAPI.getNewsHeadlines();
        if (data?.articles?.length) {
          return data.articles.map((a: any, i: number) => ({
            id: `voralis-${i}`,
            title: a.title,
            excerpt: a.summary || a.excerpt || "",
            source: a.source || "News Source",
            time: timeAgo(a.publishedAt || a.date),
            thumbnail: a.thumbnail || a.urlToImage,
            category: activeCategory,
            link: a.url,
          }));
        }
      } catch (e) { console.error("Voralis fail:", e); }
      return null;
    };

    const trySerp = async () => {
      try {
        let endpoint = "/api/news/top";
        let params: any = { gl: "in", hl: "en" };

        const cat = activeCategory.toLowerCase();

        if (cat === "search results") {
          endpoint = "/api/news/search";
          params.q = searchQuery;
        } else if (cat === "india") {
          endpoint = "/api/news/top";
          params.gl = "in";
        } else if (["world", "business", "technology", "entertainment", "sports", "science", "health"].includes(cat)) {
          endpoint = "/api/news/category";
          params.category = cat;
        } else if (cat === "home") {
          endpoint = "/api/news/top";
        }

        const r = await axios.get(`${SERP_API}${endpoint}`, {
          params,
          timeout: 15000,
        });

        const results = r.data?.articles || [];
        if (results.length) {
          return results.map((item: any, i: number) => ({
            id: `serp-${i}`,
            title: item.title,
            excerpt: item.snippet || item.snippet_highlight || "",
            source: typeof item.source === "string" ? item.source : item.source?.name || "News",
            time: timeAgo(item.iso_date || item.date),
            thumbnail: item.thumbnail || item.thumbnail_small,
            category: activeCategory,
            link: item.link,
          }));
        }
      } catch (e) { console.error("Serp fail:", e); }
      return null;
    };

    try {
      if (provider === "voralis") {
        const res = await tryVoralis();
        if (res) { data_to_set = res; success = true; }
        else {
          const alt = await trySerp();
          if (alt) { data_to_set = alt; success = true; }
        }
      } else {
        const res = await trySerp();
        if (res) { data_to_set = res; success = true; }
        else {
          const alt = await tryVoralis();
          if (alt) { data_to_set = alt; success = true; }
        }
      }
      setArticles(data_to_set);
    } catch (err) {
      console.error("News fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, provider]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
       fetchData();
       setLastRefreshed(new Date());
    }, 15000); // 15s refresh for news
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setActiveCategory("Search Results");
    }
  };

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col font-sans text-[#bdc1c6] selection:bg-[#4285f4] selection:text-white">
      {/* Google-News Style Header */}
      <header className="sticky top-0 z-50 bg-[#000000] border-b border-[#3c4043] px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-[#202124] rounded-full text-[#9aa0a6]">
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex items-center gap-1 cursor-pointer" onClick={() => setActiveCategory("Home")}>
            <span className="text-xl font-normal tracking-tight text-[#e8eaed]">
              {provider === "voralis" ? (
                <span className="flex items-center gap-1.5 font-bold">
                  <span className="bg-[#6001d2] text-white px-2 py-0.5 rounded italic">Y!</span> News
                </span>
              ) : (
                <>
                  <span className="text-[#a8c7fa]">G</span>
                  <span className="text-[#a8c7fa]">o</span>
                  <span className="text-[#a8c7fa]">o</span>
                  <span className="text-[#a8c7fa]">g</span>
                  <span className="text-[#a8c7fa]">l</span>
                  <span className="text-[#a8c7fa]">e</span>
                  <span className="ml-1 text-[18px]">News</span>
                </>
              )}
            </span>
          </div>
        </div>

        {/* Search Bar - Matching Dark Mode Reference */}
        <form onSubmit={handleSearch} className="flex-1 max-w-[720px] mx-4 relative group">
          <div className="flex items-center bg-[#202124] focus-within:bg-[#303134] focus-within:shadow-[0_1px_6px_0_rgba(0,0,0,0.5)] rounded-xl px-4 py-2.5 transition-all">
            <Search className="w-5 h-5 text-[#9aa0a6]" />
            <input
              type="text"
              placeholder="Search for topics, locations & sources"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-transparent ml-3 outline-none text-base border-none ring-0 placeholder:text-[#9aa0a6] text-[#e8eaed]"
            />
          </div>
        </form>

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end mr-2 md:flex hidden">
             <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-[9px] font-bold text-red-500 uppercase tracking-widest">Live</span>
             </div>
             <span className="text-[8px] text-[#9aa0a6]">Updated: {lastRefreshed.toLocaleTimeString()}</span>
          </div>
          <button
            onClick={() => setProvider(p => p === "serp" ? "voralis" : "serp")}
            className={cn(
              "px-4 py-1.5 text-[10px] font-bold uppercase rounded-full border transition-all",
              provider === "serp" ? "bg-[#1a3b5c] text-[#a8c7fa] border-[#a8c7fa]/20" : "bg-[#6001d2]/20 text-[#d4bafa] border-[#d4bafa]/40 hover:bg-[#6001d2]/40"
            )}
          >
            {provider === "serp" ? "SerpAPI" : "Yahoo Mirror"}
          </button>
          <button className="p-2 hover:bg-[#202124] rounded-full text-[#9aa0a6]"><Bell className="w-5 h-5" /></button>
          <button className="p-2 hover:bg-[#202124] rounded-full text-[#9aa0a6]"><Settings className="w-5 h-5" /></button>
          <button className="ml-2 w-8 h-8 rounded-full overflow-hidden border border-[#3c4043]">
            <img src="https://ui-avatars.com/api/?name=Admin&background=a8c7fa&color=000" alt="user" />
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <aside className="w-[280px] hidden md:flex flex-col bg-[#000000] border-r border-[#3c4043] overflow-y-auto py-4">
          <div className="space-y-0.5 px-3 mb-4">
            {SIDEBAR_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveCategory(item.id)}
                className={cn(
                  "w-full flex items-center gap-4 px-4 py-3 rounded-full text-[14px] font-medium transition-colors",
                  activeCategory === item.id
                    ? "bg-[#1a2b4a] text-[#a8c7fa]"
                    : "text-[#bdc1c6] hover:bg-[#202124]"
                )}
              >
                <item.icon className={cn("w-5 h-5", activeCategory === item.id ? "text-[#a8c7fa]" : "text-[#9aa0a6]")} />
                {item.label}
              </button>
            ))}
          </div>

          <div className="h-px bg-[#3c4043] mx-4 mb-4" />

          <div className="px-7 mb-2">
            <span className="text-[14px] font-medium text-[#e8eaed]">Topics</span>
          </div>
          <div className="space-y-0.5 px-3">
            {TOPICS.map((topic) => (
              <button
                key={topic.id}
                onClick={() => setActiveCategory(topic.id)}
                className={cn(
                  "w-full flex items-center gap-4 px-4 py-2.5 rounded-full text-[14px] transition-colors",
                  activeCategory === topic.id
                    ? "bg-[#1a2b4a] text-[#a8c7fa] font-medium"
                    : "text-[#bdc1c6] hover:bg-[#202124]"
                )}
              >
                <topic.icon className={cn("w-5 h-5", activeCategory === topic.id ? "text-[#a8c7fa]" : "text-[#9aa0a6]")} />
                {topic.label}
              </button>
            ))}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto bg-[#000000]">
          <div className="max-w-[1040px] mx-auto px-6 py-6">

            {/* Briefing Header */}
            <div className="mb-6">
              <h1 className="text-[28px] font-normal text-[#e8eaed] mb-1">Your briefing</h1>
              <p className="text-[14px] text-[#9aa0a6]">{new Date().toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long' })}</p>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                <div className="md:col-span-8 space-y-8">
                  <div className="bg-[#1f2023] rounded-2xl h-80 animate-pulse" />
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-[#1f2023] rounded-xl h-40 animate-pulse" />
                    <div className="bg-[#1f2023] rounded-xl h-40 animate-pulse" />
                  </div>
                </div>
                <div className="md:col-span-4 space-y-4">
                  {[1, 2, 3, 4].map(i => <div key={i} className="bg-[#1f2023] rounded-xl h-24 animate-pulse" />)}
                </div>
              </div>
            ) : articles.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-x-8 gap-y-10">

                {/* Left Side: Top Stories */}
                <div className="md:col-span-8">
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-[#a8c7fa] font-medium text-[16px] flex items-center group cursor-pointer hover:underline uppercase tracking-wider">
                        Top stories
                        <ChevronRight className="w-5 h-5 ml-1" />
                      </h2>
                    </div>

                    {/* Featured Article Card - Exact Google Layout */}
                    <article className="bg-[#1f2023]/30 border border-[#3c4043] rounded-2xl p-6 mb-8 hover:bg-[#1f2023]/60 transition-all group">
                      <div className="flex flex-col md:flex-row gap-6">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-3">
                            <span className="font-bold text-[#e8eaed] text-[13px]">{articles[0].source}</span>
                            <span className="text-[#9aa0a6] text-[13px]">{articles[0].time}</span>
                          </div>
                          <h3 className="text-[22px] font-normal leading-[1.3] text-[#e8eaed] mb-4 group-hover:underline">
                            {articles[0].title}
                          </h3>
                          <div className="flex items-center gap-4 mt-6">
                            <a href={articles[0].link} target="_blank" className="text-[14px] text-[#a8c7fa] font-medium hover:underline">Full coverage</a>
                            <div className="flex items-center gap-2 ml-auto">
                              <button className="p-2 hover:bg-[#3c4043] rounded-full text-[#9aa0a6]"><Bookmark className="w-4 h-4" /></button>
                              <button className="p-2 hover:bg-[#3c4043] rounded-full text-[#9aa0a6]"><Share2 className="w-4 h-4" /></button>
                            </div>
                          </div>
                        </div>
                        {articles[0].thumbnail && (
                          <div className="w-full md:w-[320px] h-[180px] shrink-0">
                            <img
                              src={articles[0].thumbnail}
                              alt="headline"
                              className="w-full h-full object-cover rounded-xl shadow-lg border border-[#3c4043]"
                            />
                          </div>
                        )}
                      </div>
                    </article>

                    {/* Small Article List */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-10">
                      {articles.slice(1, 9).map(item => (
                        <div key={item.id} className="group cursor-pointer">
                          <div className="flex gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-bold text-[#bdc1c6] text-[11px]">{item.source}</span>
                                <span className="text-[#9aa0a6] text-[11px]">{item.time}</span>
                              </div>
                              <h4 className="text-[15px] font-normal text-[#e8eaed] leading-tight group-hover:underline line-clamp-3 mb-3">
                                {item.title}
                              </h4>
                              <div className="flex items-center gap-2">
                                <button className="p-1.5 hover:bg-[#202124] rounded-full text-[#9aa0a6]"><Bookmark className="w-3.5 h-3.5" /></button>
                                <button className="p-1.5 hover:bg-[#202124] rounded-full text-[#9aa0a6]"><Share2 className="w-3.5 h-3.5" /></button>
                              </div>
                            </div>
                            {item.thumbnail && (
                              <img
                                src={item.thumbnail}
                                alt="thumb"
                                className="w-[100px] h-[100px] object-cover rounded-lg flex-shrink-0 border border-[#3c4043]"
                              />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Sources Section - Matching Carousel from Image */}
                    <section className="mt-16 border-t border-[#3c4043] pt-8">
                      <h2 className="text-[#e8eaed] text-[18px] mb-6">Sources</h2>
                      <div className="flex gap-4 overflow-x-auto pb-4 no-scrollbar">
                        {["The Times of India", "Hindustan Times", "NDTV", "The Hindu", "Reuters"].map(src => (
                          <div key={src} className="min-w-[160px] bg-[#1f2023] border border-[#3c4043] rounded-2xl p-4 flex flex-col items-center">
                            <div className="w-12 h-12 bg-white rounded-full mb-3 flex items-center justify-center p-2">
                              <Newspaper className="text-black" />
                            </div>
                            <span className="text-[13px] text-center font-bold text-[#e8eaed] mb-4 line-clamp-1">{src}</span>
                            <button className="w-full py-1.5 border border-[#5f6368] rounded-full text-[12px] text-[#a8c7fa] font-medium hover:bg-[#a8c7fa]/5">
                              Follow
                            </button>
                          </div>
                        ))}
                      </div>
                    </section>
                  </section>
                </div>

                {/* Right Side: Local News & Panels */}
                <div className="md:col-span-4">
                  <section className="bg-[#1f2023]/20 border border-[#3c4043] rounded-2xl overflow-hidden mb-8">
                    <div className="px-6 py-5 border-b border-[#3c4043] flex items-center justify-between">
                      <h3 className="text-[#e8eaed] font-medium flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-[#a8c7fa]" />
                        Local news
                      </h3>
                      <ChevronRight className="w-4 h-4 text-[#9aa0a6]" />
                    </div>
                    <div className="p-4 space-y-6">
                      {articles.slice(9, 12).map(item => (
                        <div key={item.id} className="flex gap-3 group cursor-pointer">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 text-[11px] mb-1">
                              <span className="font-bold text-[#bdc1c6]">{item.source}</span>
                              <span className="text-[#9aa0a6]">{item.time}</span>
                            </div>
                            <h4 className="text-[13px] text-[#e8eaed] group-hover:underline line-clamp-2 leading-snug">{item.title}</h4>
                          </div>
                          {item.thumbnail && <img src={item.thumbnail} className="w-14 h-14 object-cover rounded-lg" />}
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="bg-[#1f2023]/20 border border-[#3c4043] rounded-2xl overflow-hidden">
                    <div className="px-6 py-5 border-b border-[#3c4043] flex items-center justify-between">
                      <h3 className="text-[#e8eaed] font-medium">Picked for you</h3>
                      <LayoutGrid className="w-4 h-4 text-[#9aa0a6]" />
                    </div>
                    <div className="p-4 space-y-6">
                      {articles.slice(12, 16).map(item => (
                        <div key={item.id} className="flex flex-col group cursor-pointer border-b border-[#3c4043] last:border-0 pb-4">
                          <div className="flex items-center gap-2 text-[11px] mb-1">
                            <span className="font-bold text-[#bdc1c6]">{item.source}</span>
                            <span className="text-[#9aa0a6]">{item.time}</span>
                          </div>
                          <h4 className="text-[14px] text-[#e8eaed] group-hover:underline line-clamp-2 leading-relaxed">{item.title}</h4>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>

              </div>
            ) : null}
          </div>

          <footer className="max-w-[1040px] mx-auto px-6 py-12 border-t border-[#3c4043] text-center">
            <div className="flex flex-wrap justify-center gap-6 text-[12px] text-[#9aa0a6] mb-8">
              <a href="#" className="hover:text-[#e8eaed]">Help</a>
              <a href="#" className="hover:text-[#e8eaed]">Send feedback</a>
              <a href="#" className="hover:text-[#e8eaed]">Privacy</a>
              <a href="#" className="hover:text-[#e8eaed]">Terms</a>
              <a href="#" className="hover:text-[#e8eaed]">Disclaimer</a>
            </div>
            <p className="text-[11px] text-[#5f6368]">Developed for AARAMBH Ecosystem | Intelligence Module</p>
          </footer>
        </main>
      </div>
    </div>
  );
}
