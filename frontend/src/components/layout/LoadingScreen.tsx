import { useState, useEffect } from "react";
import { Bot } from "lucide-react";

interface LoadingScreenProps {
  message?: string;
}

const OLLO_STEPS = [
  "Loading...",
  "OLLO is analyzing...",
  "Evaluating Whale Activity...",
  "Reading Market Structure...",
  "Consensus in progress...",
  "Synthesizing Evidence...",
  "Assessing Portfolio Exposure...",
  "Consulting Council Consensus..."
];

export function LoadingScreen({ message }: LoadingScreenProps) {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  useEffect(() => {
    // Cycle through OLLO steps every 2 seconds
    const interval = setInterval(() => {
      setCurrentStepIdx((prev) => (prev + 1) % OLLO_STEPS.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const displayMessage = message || OLLO_STEPS[currentStepIdx];

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[300px] gap-6 p-8 text-center bg-[#0B1220]/20 rounded-xl">
      {/* Dynamic OLLO breathing ring */}
      <div
        className="relative flex items-center justify-center w-16 h-16 rounded-full bg-[#101A2E] border border-[var(--border-subtle)] overflow-hidden shadow-[0_0_20px_rgba(59,130,246,0.25)]"
        style={{
          animation: "ollo-breathe 3s ease-in-out infinite, ollo-glow 3s ease-in-out infinite"
        }}
      >
        <div className="absolute inset-0 bg-radial-gradient from-blue-500/10 via-transparent to-transparent pointer-events-none" />
        <Bot className="w-7 h-7 text-blue-400 animate-pulse" />
      </div>

      <div className="flex flex-col items-center gap-3">
        {/* Breathing dots */}
        <div className="flex gap-1.5 justify-center">
          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>

        <p className="text-xs font-mono font-medium text-[var(--accent-blue)] uppercase tracking-wider min-h-[1.5rem] animate-pulse">
          {displayMessage}
        </p>
      </div>
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-[var(--accent-blue)]"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}
