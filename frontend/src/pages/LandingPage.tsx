import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Newspaper,
  Globe,
  Database,
  ArrowRight,
  Zap,
  Activity,
  Cpu,
  Terminal,
  ChevronRight,
  Layers,
  BarChart3,
  Network,
  Shield,
  Radar,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { GlobeComponent } from "@/components/ui/globe";

const stagger = {
  container: { animate: { transition: { staggerChildren: 0.08 } } },
  item: {
    initial: { opacity: 0, y: 20 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] },
    },
  },
};

export default function LandingPage() {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  return (
    <div className="min-h-screen bg-[#030305] text-white selection:bg-violet-500/20 overflow-x-hidden">
      {/* ── Fixed ambient background ───────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-20%] left-[-8%] w-[60%] h-[70%] bg-violet-700/[0.06] blur-[200px] rounded-full" />
        <div className="absolute bottom-[-20%] right-[-8%] w-[55%] h-[65%] bg-blue-700/[0.06] blur-[200px] rounded-full" />
        <div className="absolute top-[45%] left-[25%] w-[45%] h-[45%] bg-emerald-700/[0.04] blur-[160px] rounded-full" />
        {/* Grid */}
        <div
          className="absolute inset-0 opacity-[0.016]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />
        {/* Radial vignette */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_50%,transparent_20%,#030305_90%)] opacity-60" />
      </div>

      <div className="relative z-10">
        {/* ══════════════════════════════════════════════════════════════
            HERO — Architecture image background
        ══════════════════════════════════════════════════════════════ */}
        <motion.section
          variants={stagger.container}
          initial="initial"
          animate="animate"
          className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center overflow-hidden"
        >
          {/* ── Architecture image background ── */}
          <div className="absolute inset-0 z-0">
            {/* Image layer */}
            <div
              className="absolute inset-0 bg-center bg-no-repeat"
              style={{
                backgroundImage: "url('/architecture-bg.png')",
                backgroundSize: "70%",
                backgroundPosition: "center 60%",
                opacity: 0.18,
                filter: "saturate(1.4) brightness(0.9)",
              }}
            />
            {/* Top fade */}
            <div className="absolute inset-0 bg-gradient-to-b from-[#030305] via-[#030305]/30 to-[#030305]" />
            {/* Side fades */}
            <div className="absolute inset-0 bg-gradient-to-r from-[#030305]/80 via-transparent to-[#030305]/80" />
            {/* Centre radial reveal */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_55%_at_50%_60%,transparent_0%,#030305_100%)]" />
          </div>

          {/* ── Content ── */}
          <div className="relative z-10 flex flex-col items-center max-w-5xl mx-auto">
            {/* Status pill */}
            <motion.div
              variants={stagger.item}
              className="inline-flex items-center gap-3 px-5 py-2 rounded-full bg-white/[0.03] border border-white/[0.08] mb-10 backdrop-blur-xl shadow-[0_0_40px_rgba(167,139,250,0.06),inset_0_1px_0_rgba(255,255,255,0.06)]"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_#34d399]" />
              <span className="text-[10px] font-black uppercase tracking-[0.25em] text-white/40">
                Intelligence Platform Active
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse shadow-[0_0_10px_#a78bfa]" />
            </motion.div>

            {/* Wordmark */}
            <motion.h1
              variants={stagger.item}
              className="text-[7rem] md:text-[11rem] font-black tracking-[-0.07em] leading-[0.82] mb-5 select-none"
            >
              <span
                className="text-transparent bg-clip-text"
                style={{
                  backgroundImage:
                    "linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.75) 60%, rgba(255,255,255,0.25) 100%)",
                  filter: "drop-shadow(0 0 80px rgba(167,139,250,0.18))",
                }}
              >
                AARAMBH
              </span>
            </motion.h1>

            {/* Shimmering divider */}
            <motion.div variants={stagger.item} className="relative mb-8">
              <div className="h-px w-56 bg-gradient-to-r from-transparent via-violet-400/70 to-transparent" />
              <div className="absolute inset-0 h-px w-56 bg-gradient-to-r from-transparent via-white/30 to-transparent blur-sm" />
            </motion.div>

            <motion.p
              variants={stagger.item}
              className="text-base md:text-lg text-white/18 font-black uppercase tracking-[0.35em] mb-10"
            >
              Intelligence Terminal
            </motion.p>

            <motion.p
              variants={stagger.item}
              className="max-w-xl text-sm text-white/30 leading-relaxed mb-14"
            >
              Real-time news intelligence, financial analytics, geopolitical
              monitoring, and ontology-driven simulation — unified in a single
              command surface.
            </motion.p>

            {/* CTAs */}
            <motion.div
              variants={stagger.item}
              className="flex flex-wrap items-center justify-center gap-4 mb-16"
            >
              <button
                onClick={() => navigate("/f2")}
                className="h-14 px-10 rounded-xl flex items-center gap-3 font-black uppercase tracking-[0.15em] text-[11px] transition-all hover:scale-[1.03] active:scale-[0.97]"
                style={{
                  background:
                    "linear-gradient(135deg, #7c3aed 0%, #6d28d9 50%, #5b21b6 100%)",
                  boxShadow:
                    "0 0 50px rgba(124,58,237,0.4), 0 0 120px rgba(124,58,237,0.15), inset 0 1px 0 rgba(255,255,255,0.15)",
                  border: "1px solid rgba(167,139,250,0.3)",
                }}
              >
                Enter Terminal <Terminal className="w-4 h-4" />
              </button>
              <button
                onClick={() => window.open("http://localhost:3000", "_blank")}
                className="h-14 px-10 bg-white/[0.04] border border-white/[0.09] text-white/55 rounded-xl flex items-center gap-3 font-black uppercase tracking-[0.15em] text-[11px] hover:bg-white/[0.07] hover:border-white/[0.15] hover:text-white/80 transition-all backdrop-blur-sm"
                style={{
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)",
                }}
              >
                Ontology Engine <Database className="w-4 h-4" />
              </button>
            </motion.div>

            {/* Micro stats */}
            <motion.div
              variants={stagger.item}
              className="flex items-center gap-10"
            >
              {[
                { value: "LIVE", label: "Feed Status", color: "#34d399" },
                { value: "4+", label: "Intel Modules", color: "#a78bfa" },
                { value: "AI", label: "Powered Core", color: "#38bdf8" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="flex flex-col items-center gap-1.5"
                >
                  <span
                    className="text-xl font-black tracking-wider"
                    style={{
                      color: stat.color,
                      textShadow: `0 0 20px ${stat.color}60`,
                    }}
                  >
                    {stat.value}
                  </span>
                  <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
                    {stat.label}
                  </span>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Architecture image label callouts — decorative */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 1 }}
            className="absolute bottom-28 left-1/2 -translate-x-1/2 w-full max-w-4xl pointer-events-none hidden md:flex justify-between px-12"
          >
            {[
              "Enterprise Data",
              "Governance",
              "Ontology + Toolchain",
              "Agent Layer",
            ].map((lbl) => (
              <span
                key={lbl}
                className="text-[8px] font-black uppercase tracking-[0.25em] text-white/12 border-b border-white/8 pb-1"
              >
                {lbl}
              </span>
            ))}
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.8 }}
            className="absolute bottom-8 flex flex-col items-center gap-2"
          >
            <span className="text-[8px] font-black uppercase tracking-[0.4em] text-white/10">
              Scroll
            </span>
            <div className="w-px h-10 bg-gradient-to-b from-white/15 to-transparent" />
          </motion.div>
        </motion.section>

        {/* ══════════════════════════════════════════════════════════════
            VIDEO SHOWCASE — Full highlight section
        ══════════════════════════════════════════════════════════════ */}
        <section className="relative py-32 overflow-hidden">
          {/* Section ambient */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-violet-500/20 to-transparent" />
            <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-violet-500/10 to-transparent" />
            <div className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[900px] h-[500px] bg-violet-800/[0.05] blur-[160px] rounded-full" />
          </div>

          <div className="relative max-w-[1400px] mx-auto px-6">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="text-center mb-14"
            >
              <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-red-500/[0.08] border border-red-500/20 mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse shadow-[0_0_8px_#f87171]" />
                <span className="text-[9px] font-black uppercase tracking-[0.25em] text-red-400/80">
                  Live Demo
                </span>
              </div>
              <h2 className="text-4xl md:text-6xl font-black tracking-tight mb-5">
                <span
                  className="text-transparent bg-clip-text"
                  style={{
                    backgroundImage:
                      "linear-gradient(135deg, #ffffff 0%, rgba(255,255,255,0.6) 100%)",
                  }}
                >
                  SEE IT IN ACTION
                </span>
              </h2>
              <p className="text-sm text-white/30 max-w-lg mx-auto leading-relaxed">
                Watch AARAMBH process live intelligence streams, classify
                geopolitical signals, and synthesise multi-domain insights in
                real time.
              </p>
            </motion.div>

            {/* Video player */}
            <motion.div
              initial={{ opacity: 0, y: 30, scale: 0.98 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="relative max-w-5xl mx-auto group"
            >
              {/* Outer glow ring */}
              <div
                className="absolute -inset-px rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(124,58,237,0.5) 0%, rgba(56,189,248,0.3) 50%, rgba(52,211,153,0.3) 100%)",
                  filter: "blur(1px)",
                }}
              />
              {/* Ambient glow */}
              <div
                className="absolute -inset-8 rounded-3xl opacity-40 group-hover:opacity-70 transition-opacity duration-700 pointer-events-none"
                style={{
                  background:
                    "radial-gradient(ellipse at center, rgba(124,58,237,0.15) 0%, transparent 70%)",
                  filter: "blur(20px)",
                }}
              />

              {/* Player frame */}
              <div
                className="relative rounded-2xl overflow-hidden border border-white/[0.1] group-hover:border-violet-500/30 transition-colors duration-500"
                style={{
                  background:
                    "linear-gradient(180deg, #0a0a12 0%, #060608 100%)",
                  boxShadow:
                    "0 30px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.06)",
                }}
              >
                {/* Titlebar chrome */}
                <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500/70 hover:bg-red-500 transition-colors cursor-pointer" />
                    <div className="w-3 h-3 rounded-full bg-amber-400/70 hover:bg-amber-400 transition-colors cursor-pointer" />
                    <div className="w-3 h-3 rounded-full bg-emerald-400/70 hover:bg-emerald-400 transition-colors cursor-pointer" />
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-white/[0.03] border border-white/[0.06]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-white/25">
                      aarambh-intelligence-terminal
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-6 h-6 rounded-md bg-white/[0.03] border border-white/[0.06] flex items-center justify-center cursor-pointer hover:bg-white/[0.06] transition-colors">
                      <Maximize2 className="w-3 h-3 text-white/30" />
                    </div>
                  </div>
                </div>

                {/* Video */}
                <div className="relative aspect-video bg-black">
                  <video
                    ref={videoRef}
                    autoPlay
                    loop
                    muted
                    playsInline
                    className="w-full h-full object-cover opacity-95"
                    style={{
                      filter: "brightness(1.05) contrast(1.05) saturate(1.1)",
                    }}
                  >
                    <source src="/videos/hero_bg.mp4" type="video/mp4" />
                  </video>

                  {/* Subtle scanline overlay */}
                  <div
                    className="absolute inset-0 pointer-events-none opacity-[0.03]"
                    style={{
                      backgroundImage:
                        "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.8) 2px, rgba(0,0,0,0.8) 4px)",
                    }}
                  />

                  {/* Corner accent */}
                  <div className="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-md border border-white/10">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse shadow-[0_0_6px_#f87171]" />
                    <span className="text-[9px] font-black uppercase tracking-widest text-white/50">
                      Live Feed
                    </span>
                  </div>
                </div>

                {/* Control bar */}
                <div className="flex items-center justify-between px-5 py-3 border-t border-white/[0.05]">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={togglePlay}
                      className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center hover:bg-white/[0.08] hover:border-white/[0.14] transition-all"
                    >
                      {isPlaying ? (
                        <Pause className="w-3.5 h-3.5 text-white/60" />
                      ) : (
                        <Play className="w-3.5 h-3.5 text-white/60" />
                      )}
                    </button>
                    <button
                      onClick={toggleMute}
                      className="w-8 h-8 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center hover:bg-white/[0.08] hover:border-white/[0.14] transition-all"
                    >
                      {isMuted ? (
                        <VolumeX className="w-3.5 h-3.5 text-white/60" />
                      ) : (
                        <Volume2 className="w-3.5 h-3.5 text-white/60" />
                      )}
                    </button>
                    <span className="text-[9px] font-black uppercase tracking-widest text-white/20">
                      AARAMBH Platform Demo
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {["HD", "AI", "LIVE"].map((tag) => (
                      <span
                        key={tag}
                        className="text-[8px] font-black px-1.5 py-0.5 rounded border border-white/10 text-white/25 uppercase tracking-wider"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Feature callouts below video */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-10 grid grid-cols-3 gap-4 max-w-2xl mx-auto"
            >
              {[
                {
                  icon: Radar,
                  label: "Real-time signal monitoring",
                  color: "#a78bfa",
                },
                {
                  icon: Activity,
                  label: "Multi-domain analytics",
                  color: "#38bdf8",
                },
                {
                  icon: Shield,
                  label: "Sovereign intelligence layer",
                  color: "#34d399",
                },
              ].map((f) => (
                <div
                  key={f.label}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/[0.06] bg-white/[0.02] text-center"
                >
                  <f.icon className="w-4 h-4" style={{ color: f.color }} />
                  <span className="text-[9px] font-bold uppercase tracking-widest text-white/25 leading-snug">
                    {f.label}
                  </span>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════════════════════
            FEATURE GRID
        ══════════════════════════════════════════════════════════════ */}
        <section className="max-w-[1400px] mx-auto px-6 py-24 border-t border-white/[0.04]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="mb-14"
          >
            <div className="flex items-center gap-3 text-[10px] font-black text-white/20 uppercase tracking-[0.3em] mb-4">
              <Layers className="w-3.5 h-3.5 text-violet-400" />
              Core Modules
            </div>
            <h2
              className="text-4xl md:text-5xl font-black tracking-tight text-transparent bg-clip-text"
              style={{
                backgroundImage:
                  "linear-gradient(135deg, #ffffff 0%, rgba(255,255,255,0.45) 100%)",
              }}
            >
              UNIFIED INTELLIGENCE
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: Newspaper,
                title: "News Intelligence",
                desc: "Real-time geopolitical feed with AI analysis, sentiment scoring, and domain classification.",
                path: "/f2",
                color: "#a78bfa",
                glow: "rgba(167,139,250,0.12)",
                tag: "F2",
              },
              {
                icon: BarChart3,
                title: "Financial Analytics",
                desc: "Live market data, economic indicators, portfolio tracking and macro dashboards.",
                path: "/finance",
                color: "#34d399",
                glow: "rgba(52,211,153,0.12)",
                tag: "F3",
              },
              {
                icon: Globe,
                title: "Global View",
                desc: "3D geospatial visualisation of events and intelligence data mapped across regions.",
                path: "/globe",
                color: "#38bdf8",
                glow: "rgba(56,189,248,0.12)",
                tag: "F4",
              },
              {
                icon: Database,
                title: "Ontology Engine",
                desc: "Build knowledge graphs, simulate agents, generate strategic reports from any document.",
                path: "/ontology",
                color: "#fbbf24",
                glow: "rgba(251,191,36,0.12)",
                tag: "F5",
              },
            ].map((mod, i) => (
              <motion.div
                key={mod.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.09, duration: 0.4 }}
                onClick={() => navigate(mod.path)}
                className="group p-6 rounded-2xl cursor-pointer transition-all duration-300 relative overflow-hidden"
                style={{
                  background: "rgba(255,255,255,0.018)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.background =
                    "rgba(255,255,255,0.035)";
                  (e.currentTarget as HTMLDivElement).style.border =
                    `1px solid rgba(255,255,255,0.13)`;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.background =
                    "rgba(255,255,255,0.018)";
                  (e.currentTarget as HTMLDivElement).style.border =
                    "1px solid rgba(255,255,255,0.07)";
                }}
              >
                {/* Shiny top edge */}
                <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                {/* Hover glow */}
                <div
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl pointer-events-none"
                  style={{
                    background: `radial-gradient(ellipse at 50% 0%, ${mod.glow}, transparent 65%)`,
                  }}
                />

                <div className="flex items-center justify-between mb-5">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center border border-white/[0.07] relative overflow-hidden"
                    style={{ background: `${mod.color}14` }}
                  >
                    <mod.icon
                      className="w-5 h-5 relative z-10"
                      style={{ color: mod.color }}
                    />
                  </div>
                  <span className="text-[8px] font-black font-mono text-white/15 uppercase tracking-widest">
                    {mod.tag}
                  </span>
                </div>

                <h3 className="text-sm font-black uppercase tracking-wide text-white/65 mb-2 group-hover:text-white transition-colors">
                  {mod.title}
                </h3>
                <p className="text-[11px] text-white/25 leading-relaxed">
                  {mod.desc}
                </p>

                <div className="mt-5 flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-white/15 group-hover:text-violet-400 transition-colors">
                  Launch{" "}
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ══════════════════════════════════════════════════════════════
            ONTOLOGY SPOTLIGHT
        ══════════════════════════════════════════════════════════════ */}
        <section className="max-w-[1400px] mx-auto px-6 py-24 border-t border-white/[0.04]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
          >
            <div className="grid lg:grid-cols-2 gap-14 items-center">
              <div className="space-y-8">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/[0.08] border border-amber-500/20">
                  <Zap className="w-3 h-3 text-amber-400" />
                  <span className="text-[9px] font-black uppercase tracking-widest text-amber-400/80">
                    Simulation Engine
                  </span>
                </div>

                <h2 className="text-4xl md:text-5xl font-black tracking-tight leading-[1.08]">
                  PREDICT THE FUTURE
                  <br />
                  <span
                    className="text-transparent bg-clip-text"
                    style={{
                      backgroundImage:
                        "linear-gradient(90deg, #a78bfa 0%, #38bdf8 50%, #34d399 100%)",
                    }}
                  >
                    WITH PARALLEL WORLDS
                  </span>
                </h2>

                <p className="text-sm text-white/30 leading-relaxed max-w-lg">
                  Upload any report or document. The Ontology Engine extracts
                  entities, builds a knowledge graph, spawns agent cohorts, and
                  runs multi-platform simulations to surface hidden patterns and
                  strategic insights.
                </p>

                <button
                  onClick={() => window.open("http://localhost:3000", "_blank")}
                  className="h-12 px-8 bg-white/[0.03] border border-white/[0.08] text-white/50 rounded-xl flex items-center gap-3 font-black uppercase tracking-[0.12em] text-[10px] hover:bg-white/[0.06] hover:border-white/[0.15] hover:text-white/75 transition-all"
                  style={{ boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)" }}
                >
                  Launch Ontology Engine <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Pipeline card */}
              <div
                className="p-8 rounded-2xl relative overflow-hidden"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0.01) 100%)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)",
                }}
              >
                <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-violet-500/25 to-transparent" />
                <div className="space-y-1">
                  {[
                    {
                      num: "01",
                      title: "Graph Reconstruction",
                      desc: "Semantic extraction & knowledge graph",
                      icon: Database,
                      color: "#a78bfa",
                    },
                    {
                      num: "02",
                      title: "Environment Setup",
                      desc: "Agent profiling & platform configuration",
                      icon: Cpu,
                      color: "#38bdf8",
                    },
                    {
                      num: "03",
                      title: "Execution Phase",
                      desc: "Multi-agent recursive simulation",
                      icon: Activity,
                      color: "#34d399",
                    },
                    {
                      num: "04",
                      title: "Intelligence Report",
                      desc: "AI-synthesised analytical report",
                      icon: BarChart3,
                      color: "#fbbf24",
                    },
                    {
                      num: "05",
                      title: "Deep Interaction",
                      desc: "Interrogate agents & survey consensus",
                      icon: Terminal,
                      color: "#f472b6",
                    },
                  ].map((step, i) => (
                    <div
                      key={step.num}
                      className="flex items-center gap-4 p-4 rounded-xl hover:bg-white/[0.03] transition-colors group cursor-default"
                    >
                      <div
                        className="w-9 h-9 rounded-lg flex items-center justify-center font-black text-xs flex-shrink-0 border"
                        style={
                          i === 0
                            ? {
                                background: "rgba(167,139,250,0.1)",
                                border: "1px solid rgba(167,139,250,0.25)",
                                color: step.color,
                              }
                            : {
                                background: "rgba(255,255,255,0.02)",
                                border: "1px solid rgba(255,255,255,0.06)",
                                color: "rgba(255,255,255,0.2)",
                              }
                        }
                      >
                        {step.num}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[11px] font-black uppercase tracking-wide text-white/45 group-hover:text-white/75 transition-colors">
                          {step.title}
                        </h4>
                        <p className="text-[9px] text-white/18 uppercase tracking-wider">
                          {step.desc}
                        </p>
                      </div>
                      <step.icon className="w-4 h-4 text-white/[0.06] group-hover:text-white/18 transition-colors flex-shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* ══════════════════════════════════════════════════════════════
            GLOBE — Worldwide Intelligence
        ══════════════════════════════════════════════════════════════ */}
        <section className="max-w-[1400px] mx-auto px-6 py-24 border-t border-white/[0.04]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.7 }}
          >
            {/* Header */}
            <div className="text-center mb-14 space-y-4">
              <div className="flex items-center justify-center gap-3 text-[10px] font-black text-white/20 uppercase tracking-[0.3em]">
                <Radar className="w-3.5 h-3.5 text-emerald-400" />
                Global Coverage
              </div>
              <h2
                className="text-4xl md:text-5xl font-black tracking-tight text-transparent bg-clip-text"
                style={{
                  backgroundImage:
                    "linear-gradient(135deg, #ffffff 0%, rgba(255,255,255,0.4) 100%)",
                }}
              >
                WORLDWIDE INTELLIGENCE
              </h2>
              <p className="text-sm text-white/25 max-w-lg mx-auto leading-relaxed">
                Monitoring every meridian. Real-time signals flowing across the
                global intelligence mesh — from geopolitical events to financial
                tremors.
              </p>
            </div>

            {/* Globe */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div
                  className="w-[700px] h-[350px] rounded-full"
                  style={{
                    background:
                      "radial-gradient(ellipse at center, rgba(124,58,237,0.08) 0%, rgba(56,189,248,0.04) 50%, transparent 70%)",
                    filter: "blur(60px)",
                  }}
                />
              </div>

              <div className="relative z-10">
                <GlobeComponent className="mx-auto" />
              </div>

              {/* Stat chips */}
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="mt-10 grid grid-cols-3 gap-4 max-w-2xl mx-auto"
              >
                {[
                  {
                    icon: Network,
                    value: "MULTI-SOURCE",
                    label: "Data Ingestion",
                    color: "#a78bfa",
                  },
                  {
                    icon: Shield,
                    value: "SOVEREIGN",
                    label: "Intelligence Layer",
                    color: "#34d399",
                  },
                  {
                    icon: Activity,
                    value: "REAL-TIME",
                    label: "Signal Processing",
                    color: "#38bdf8",
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="flex flex-col items-center gap-2.5 p-5 rounded-2xl border border-white/[0.06] bg-white/[0.018] relative overflow-hidden"
                    style={{
                      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
                    }}
                  >
                    <div
                      className="absolute top-0 left-0 w-full h-px"
                      style={{
                        background: `linear-gradient(90deg, transparent, ${item.color}40, transparent)`,
                      }}
                    />
                    <item.icon
                      className="w-5 h-5"
                      style={{
                        color: item.color,
                        filter: `drop-shadow(0 0 6px ${item.color}60)`,
                      }}
                    />
                    <span
                      className="text-xs font-black tracking-wider"
                      style={{ color: item.color }}
                    >
                      {item.value}
                    </span>
                    <span className="text-[9px] font-bold uppercase tracking-widest text-white/20">
                      {item.label}
                    </span>
                  </div>
                ))}
              </motion.div>
            </div>
          </motion.div>
        </section>

        {/* ══════════════════════════════════════════════════════════════
            FOOTER
        ══════════════════════════════════════════════════════════════ */}
        <footer className="border-t border-white/[0.04] py-14 px-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/6 to-transparent" />
          <div className="max-w-[1400px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <span
                className="text-xl font-black tracking-tight text-transparent bg-clip-text"
                style={{
                  backgroundImage:
                    "linear-gradient(135deg, rgba(255,255,255,0.65) 0%, rgba(255,255,255,0.2) 100%)",
                }}
              >
                AARAMBH
              </span>
              <div className="h-4 w-px bg-white/10" />
              <span className="text-[8px] font-black uppercase tracking-[0.3em] text-white/12">
                v0.1 Preview
              </span>
            </div>

            <p className="text-[10px] text-white/15 font-medium">
              India's Sovereign Intelligence Terminal
            </p>

            <div className="flex items-center gap-6">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] font-black uppercase tracking-widest text-white/15 hover:text-white/40 transition-colors"
              >
                GitHub
              </a>
              <a
                href="#"
                className="text-[10px] font-black uppercase tracking-widest text-white/15 hover:text-white/40 transition-colors"
              >
                Docs
              </a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
