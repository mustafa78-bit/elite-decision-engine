import { useEffect, useState } from 'react';
import OLLOCommander from './OLLOCommander';
import type { OLLOResponse, OLLOBriefing } from '../../types/ollo';
import brainVideo from '../../assets/crystal_brain.mp4';

export interface NexusDashboardProps {
  olloGreeting: OLLOResponse | null;
  olloBriefing: OLLOBriefing | null;
  olloLoading: boolean;
  olloError: string | null;
  onEnterCommandDeck?: () => void;
}

export const NexusDashboard: React.FC<NexusDashboardProps> = ({
  olloGreeting,
  olloBriefing,
  olloLoading,
  olloError,
  onEnterCommandDeck,
}) => {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => setTime(new Date().toISOString().substring(11, 19) + ' UTC');
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative w-full min-h-[92vh] bg-[#04070d] text-slate-200 font-sans overflow-hidden select-none flex flex-col">
      <style>{`
        @keyframes nexus-ripple {
          0% { transform: scale(0.7); opacity: 0.5; }
          100% { transform: scale(1.9); opacity: 0; }
        }
        .nexus-ripple-1 { animation: nexus-ripple 4.5s cubic-bezier(0.1, 0.8, 0.3, 1) infinite; }
        .nexus-ripple-2 { animation: nexus-ripple 4.5s cubic-bezier(0.1, 0.8, 0.3, 1) infinite 1.5s; }
        .nexus-ripple-3 { animation: nexus-ripple 4.5s cubic-bezier(0.1, 0.8, 0.3, 1) infinite 3s; }
      `}</style>

      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_10%,rgba(6,182,212,0.10),transparent_60%)] pointer-events-none" />

      {/* Minimal top status bar */}
      <header className="relative z-20 flex items-center justify-between px-8 pt-7">
        <span className="flex items-center gap-2 text-[11px] font-mono tracking-widest text-cyan-400/80 uppercase">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          system optimal
        </span>
        <span className="text-[13px] font-mono tracking-[0.4em] text-slate-100">NEXUS</span>
        <span className="text-[11px] font-mono tracking-wider text-cyan-400/60 tabular-nums">{time || '10:10:30 UTC'}</span>
      </header>

      {/* Brain hero — no side cards, just the brain */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 py-10 text-center">
        <div className="relative w-[min(440px,72vw)] aspect-square">
          <span className="nexus-ripple-1 absolute inset-0 rounded-full border border-cyan-400/25" />
          <span className="nexus-ripple-2 absolute inset-0 rounded-full border border-cyan-400/20" />
          <span className="nexus-ripple-3 absolute inset-0 rounded-full border border-cyan-400/15" />
          <div className="absolute inset-0 rounded-full overflow-hidden shadow-[0_0_90px_10px_rgba(34,211,238,0.12)]">
            <video
              autoPlay
              muted
              loop
              playsInline
              className="w-full h-full object-cover"
              src={brainVideo}
            />
            <div className="absolute inset-0 rounded-full pointer-events-none" style={{ boxShadow: 'inset 0 0 60px 20px #04070d' }} />
          </div>
        </div>

        {/* OLLO conversation lives right under the brain */}
        <div className="mt-2 w-full flex justify-center">
          <OLLOCommander
            greeting={olloGreeting}
            briefing={olloBriefing}
            loading={olloLoading}
            error={olloError}
          />
        </div>

        {onEnterCommandDeck && (
          <button
            onClick={onEnterCommandDeck}
            className="mt-10 inline-flex items-center gap-2 rounded-full border border-cyan-500/25 px-4 py-2 text-[10.5px] font-mono uppercase tracking-wider text-slate-400 hover:text-cyan-300 hover:border-cyan-400/50 transition-colors"
          >
            Command deck (full dashboard)
            <span className="text-cyan-400 font-semibold">&darr;</span>
          </button>
        )}
      </main>
    </div>
  );
};

export default NexusDashboard;
