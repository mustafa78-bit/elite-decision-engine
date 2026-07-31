import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Cpu,
  Activity,
  ShieldAlert,
  CheckCircle2,
  BarChart2,
  FileText,
  Briefcase,
  Sliders,
  Zap,
  Radio,
} from 'lucide-react';
import OLLOCommander from './OLLOCommander';
import type { OLLOResponse, OLLOBriefing } from '../../types/ollo';

export interface NexusDashboardProps {
  olloGreeting: OLLOResponse | null;
  olloBriefing: OLLOBriefing | null;
  olloLoading: boolean;
  olloError: string | null;
}

export const NexusDashboard: React.FC<NexusDashboardProps> = ({
  olloGreeting,
  olloBriefing,
  olloLoading,
  olloError,
}) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toISOString().substring(11, 19) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative min-h-screen w-full bg-[#030712] text-slate-200 font-sans overflow-hidden select-none flex flex-col justify-between p-4 md:p-6">

      {/* Dynamic Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-slate-950 to-black pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:32px_32px] opacity-10 pointer-events-none" />

      {/* Custom Styles & Keyframe Animations */}
      <style>{`
        @keyframes pulse-slow {
          0%, 100% { transform: scale(1); opacity: 0.95; filter: drop-shadow(0 0 25px rgba(6,182,212,0.6)); }
          50% { transform: scale(1.03); opacity: 1; filter: drop-shadow(0 0 45px rgba(59,130,246,0.8)); }
        }
        @keyframes ripple {
          0% { transform: scale(0.6) rotateX(75deg); opacity: 0.8; }
          100% { transform: scale(2.2) rotateX(75deg); opacity: 0; }
        }
        @keyframes waveform {
          0%, 100% { height: 6px; }
          50% { height: 28px; }
        }
        @keyframes neural-pulse {
          0% { stroke-dashoffset: 260; }
          100% { stroke-dashoffset: 0; }
        }
        .animate-brain { animation: pulse-slow 5s ease-in-out infinite; }
        .animate-ripple-1 { animation: ripple 4s cubic-bezier(0.1, 0.8, 0.3, 1) infinite; }
        .animate-ripple-2 { animation: ripple 4s cubic-bezier(0.1, 0.8, 0.3, 1) infinite 1.3s; }
        .animate-ripple-3 { animation: ripple 4s cubic-bezier(0.1, 0.8, 0.3, 1) infinite 2.6s; }
        .neural-line {
          stroke-dasharray: 10 250;
          animation: neural-pulse linear infinite;
        }
        .glass-panel {
          background: rgba(15, 23, 42, 0.55);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(56, 189, 248, 0.15);
          box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 0 12px 0 rgba(56, 189, 248, 0.05);
        }
      `}</style>

      {/* 1. TOP HEADER BAR */}
      <header className="relative z-20 flex flex-wrap items-center justify-between border-b border-cyan-500/20 pb-4 px-2">
        {/* Left Status */}
        <div className="flex items-center gap-2 text-xs font-mono tracking-wider text-cyan-400">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="h-2 w-2 rounded-full bg-emerald-400 -ml-4" />
          <span className="text-slate-400">SYSTEM STATUS:</span>
          <span className="font-bold text-emerald-400">OPTIMAL</span>
        </div>

        {/* Navigation / Logo Center */}
        <div className="flex flex-col items-center">
          {/* Main Nav Items */}
          <div className="hidden md:flex items-center gap-6 text-xs font-medium tracking-widest text-slate-400 mb-1">
            <button className="text-cyan-400 border-b border-cyan-400 pb-0.5">OVERVIEW</button>
            <button className="hover:text-slate-200 transition">ANALYTICS</button>
            <button className="hover:text-slate-200 transition">MARKETS</button>
            <button className="hover:text-slate-200 transition">OPERATING</button>
            <button className="hover:text-slate-200 transition">SETTINGS</button>
          </div>
          <h1 className="text-2xl font-black tracking-[0.35em] text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-200 to-blue-500 uppercase drop-shadow-[0_0_15px_rgba(6,182,212,0.5)]">
            NEXUS
          </h1>
          <span className="text-[9px] font-mono tracking-[0.4em] text-cyan-400/70 -mt-1">
            AI OPERATING SYSTEM
          </span>
        </div>

        {/* Right Sync */}
        <div className="flex items-center gap-3 text-xs font-mono text-cyan-400">
          <div className="flex items-center gap-1.5 bg-cyan-950/40 border border-cyan-500/30 px-2.5 py-1 rounded">
            <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
            <span className="text-[10px] text-slate-300">LIVE SYNC</span>
          </div>
          <span className="text-slate-300">{time || '10:18:30 UTC'}</span>
        </div>
      </header>

      {/* MAIN DASHBOARD CONTENT */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-4 my-auto items-center py-4">

        {/* 2. LEFT SIDEBAR PANELS */}
        <div className="lg:col-span-3 flex flex-col gap-3">
          {/* Market Regime */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Market Regime</span>
              <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-cyan-300 font-mono">REGIME: HIGH-GROWTH (92%)</div>
            <div className="w-full bg-slate-800/80 h-1.5 rounded-full mt-2 overflow-hidden border border-cyan-500/20">
              <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full w-[92%]" />
            </div>
          </div>

          {/* BTC Trend */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">BTC Trend</span>
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400 font-mono">BTC: BULLISH (MA CROSS)</div>
          </div>

          {/* AI Confidence */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">AI Confidence</span>
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-cyan-300 font-mono">CONFIDENCE: 98.4%</div>
          </div>

          {/* Whale Activity */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Whale Activity</span>
              <Zap className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xs font-semibold text-slate-200 font-mono">WHALES: ACCUMULATING (HODL WAVES)</div>
          </div>

          {/* Risk Level */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Risk Level</span>
              <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400 font-mono">RISK: LOW (0.12%)</div>
          </div>
        </div>

        {/* 3. CENTER HERO: BRAIN + RIPPLES */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center relative min-h-[380px] my-4 lg:my-0">

          {/* Holographic Ripple Platform */}
          <div className="absolute top-[65%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 pointer-events-none flex items-center justify-center">
            <div className="absolute w-64 h-64 rounded-full border border-cyan-400/40 animate-ripple-1" />
            <div className="absolute w-64 h-64 rounded-full border border-cyan-500/30 animate-ripple-2" />
            <div className="absolute w-64 h-64 rounded-full border border-blue-500/20 animate-ripple-3" />
            <div className="absolute w-40 h-40 rounded-full bg-cyan-500/10 blur-xl" />
          </div>

          {/* Glowing Crystal Brain Graphic */}
          <div className="relative z-10 animate-brain flex items-center justify-center">
            {/* SVG Brain Representation with Glass/Neural Mesh styling */}
            <svg viewBox="0 0 200 160" className="w-72 h-60 md:w-80 md:h-64 drop-shadow-[0_0_35px_rgba(6,182,212,0.7)]">
              <defs>
                <linearGradient id="brainGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.9" />
                  <stop offset="50%" stopColor="#818cf8" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.9" />
                </linearGradient>
              </defs>

              {/* Outer Brain Structure */}
              <path
                d="M 100,20 C 60,20 30,40 30,75 C 30,95 42,110 60,120 C 70,125 85,135 100,140 C 115,135 130,125 140,120 C 158,110 170,95 170,75 C 170,40 140,20 100,20 Z"
                fill="none"
                stroke="url(#brainGlow)"
                strokeWidth="2"
                className="opacity-60"
              />
              {/* Left Hemisphere Gyri */}
              <path d="M 95,25 C 70,30 45,45 42,70 C 40,90 55,105 70,115 C 80,120 92,128 95,132" fill="none" stroke="url(#brainGlow)" strokeWidth="1.5" />
              <path d="M 90,40 C 75,45 55,60 55,75 C 55,90 70,100 85,105" fill="none" stroke="url(#brainGlow)" strokeWidth="1.2" strokeDasharray="3,2" />
              <path d="M 85,55 C 70,60 62,70 65,85 C 68,95 80,98 88,90" fill="none" stroke="url(#brainGlow)" strokeWidth="1" />

              {/* Right Hemisphere Gyri */}
              <path d="M 105,25 C 130,30 155,45 158,70 C 160,90 145,105 130,115 C 120,120 108,128 105,132" fill="none" stroke="url(#brainGlow)" strokeWidth="1.5" />
              <path d="M 110,40 C 125,45 145,60 145,75 C 145,90 130,100 115,105" fill="none" stroke="url(#brainGlow)" strokeWidth="1.2" strokeDasharray="3,2" />
              <path d="M 115,55 C 130,60 138,70 135,85 C 132,95 120,98 112,90" fill="none" stroke="url(#brainGlow)" strokeWidth="1" />

              {/* Traveling neural light pulses - overlaid on the gyri paths above */}
              <path className="neural-line" style={{ animationDuration: '3.1s', animationDelay: '0s' }} d="M 95,25 C 70,30 45,45 42,70 C 40,90 55,105 70,115 C 80,120 92,128 95,132" fill="none" stroke="#a5f3fc" strokeWidth="1.8" strokeLinecap="round" />
              <path className="neural-line" style={{ animationDuration: '2.4s', animationDelay: '0.6s' }} d="M 90,40 C 75,45 55,60 55,75 C 55,90 70,100 85,105" fill="none" stroke="#a5f3fc" strokeWidth="1.5" strokeLinecap="round" />
              <path className="neural-line" style={{ animationDuration: '2.9s', animationDelay: '1.1s' }} d="M 85,55 C 70,60 62,70 65,85 C 68,95 80,98 88,90" fill="none" stroke="#a5f3fc" strokeWidth="1.3" strokeLinecap="round" />
              <path className="neural-line" style={{ animationDuration: '3.4s', animationDelay: '0.3s' }} d="M 105,25 C 130,30 155,45 158,70 C 160,90 145,105 130,115 C 120,120 108,128 105,132" fill="none" stroke="#a5f3fc" strokeWidth="1.8" strokeLinecap="round" />
              <path className="neural-line" style={{ animationDuration: '2.6s', animationDelay: '0.9s' }} d="M 110,40 C 125,45 145,60 145,75 C 145,90 130,100 115,105" fill="none" stroke="#a5f3fc" strokeWidth="1.5" strokeLinecap="round" />
              <path className="neural-line" style={{ animationDuration: '3.2s', animationDelay: '1.5s' }} d="M 115,55 C 130,60 138,70 135,85 C 132,95 120,98 112,90" fill="none" stroke="#a5f3fc" strokeWidth="1.3" strokeLinecap="round" />

              {/* Neural Nodes & Connections */}
              <circle cx="100" cy="50" r="3" fill="#67e8f9" className="animate-ping" />
              <circle cx="70" cy="70" r="2.5" fill="#38bdf8" />
              <circle cx="130" cy="70" r="2.5" fill="#38bdf8" />
              <circle cx="85" cy="95" r="2" fill="#818cf8" />
              <circle cx="115" cy="95" r="2" fill="#818cf8" />
              <circle cx="100" cy="115" r="3" fill="#67e8f9" />

              {/* Central N Badge */}
              <g transform="translate(85, 60)">
                <rect width="30" height="30" rx="6" fill="#030712" stroke="#38bdf8" strokeWidth="1.5" className="opacity-90" />
                <text x="15" y="21" textAnchor="middle" fill="#67e8f9" fontSize="16" fontWeight="bold" fontFamily="sans-serif">N</text>
              </g>
            </svg>
          </div>

          {/* Thinking Status Indicator */}
          <div className="relative z-10 flex flex-col items-center mt-2">
            <span className="text-[11px] font-mono tracking-[0.3em] text-cyan-300 font-semibold mb-2 drop-shadow">
              THINKING
            </span>

            {/* Reasoning Stages */}
            <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-cyan-500/20">
              <span className="opacity-60">Perceiving</span>
              <span className="text-cyan-500">&bull;</span>
              <span className="text-cyan-300 font-bold bg-cyan-950/80 px-2 py-0.5 rounded text-cyan-200 border border-cyan-500/40">
                Reasoning
              </span>
              <span className="text-cyan-500">&bull;</span>
              <span className="opacity-60">Learning</span>
              <span className="text-cyan-500">&bull;</span>
              <span className="opacity-60">Deciding</span>
              <span className="text-cyan-500">&bull;</span>
              <span className="opacity-60">Evolving</span>
            </div>
          </div>
        </div>

        {/* 4. RIGHT SIDEBAR PANELS */}
        <div className="lg:col-span-3 flex flex-col gap-3">
          {/* Live Decisions */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Live Decisions</span>
              <BarChart2 className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-cyan-300 font-mono">DECISIONS: 48 (ALL OPTIMAL)</div>
          </div>

          {/* Evidence Summary */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Evidence Summary</span>
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-xs font-semibold text-slate-200 font-mono">SUMMARY: 34 EVIDENCE POINTS ANALYZED</div>
          </div>

          {/* Portfolio Status */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Portfolio Status</span>
              <Briefcase className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400 font-mono">PORTFOLIO: +14.2% OVERVIEW</div>
          </div>

          {/* Active Signals */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">Active Signals</span>
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <div className="text-sm font-bold text-cyan-300 font-mono">SIGNALS: 12 BUY / 0 SELL</div>
          </div>

          {/* System Health */}
          <div className="glass-panel p-3.5 rounded-xl">
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="text-slate-400 font-medium">System Health</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-sm font-bold text-emerald-400 font-mono">HEALTH: 100% OPERATIONAL</div>
          </div>
        </div>

      </div>

      {/* 5. BOTTOM REASONING CONSOLE PANEL */}
      <footer className="relative z-20 glass-panel p-4 rounded-xl mt-auto">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono tracking-widest text-cyan-400 uppercase font-bold">
              NEXUS SPEAKS / AI REASONING CONSOLE
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-[10px] font-mono text-cyan-400/80">ACTIVE PROCESSING</span>
          </div>
        </div>

        {/* Live Speech/OLLO Commander Panel */}
        <div className="flex justify-center w-full">
          <OLLOCommander
            greeting={olloGreeting}
            briefing={olloBriefing}
            loading={olloLoading}
            error={olloError}
          />
        </div>
      </footer>

      {/* Bottom Right Decorative Sparkle */}
      <div className="absolute bottom-3 right-3 pointer-events-none opacity-40">
        <svg className="w-6 h-6 text-cyan-400" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
        </svg>
      </div>
    </div>
  );
};

export default NexusDashboard;
