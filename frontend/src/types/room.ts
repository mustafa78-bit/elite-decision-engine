export interface ParticlePreset {
  density: number;
  minSize: number;
  maxSize: number;
  speed: number;
  driftX: number;
  driftY: number;
  behavior: 'drift' | 'rise' | 'scan' | 'flow' | 'orbit' | 'ember' | 'grid';
}

export interface LightingPreset {
  ambientColor: string;
  ambientIntensity: number;
  vignetteColor: string;
  vignetteOpacity: number;
  scanlineOpacity: number;
}

export interface RoomDefinition {
  id: string;
  name: string;
  subtitle: string;
  path: string;
  accent: string;
  accentDim: string;
  accentGlow: string;
  gradient: string;
  lighting: LightingPreset;
  olloMessage: string;
  olloWelcome: string;
  parentPaths: string[];
  particles: ParticlePreset;
}

const ROOMS: Record<string, RoomDefinition> = {
  commandDeck: {
    id: 'command-deck',
    name: 'Command Deck',
    subtitle: 'Primary Operations Hub',
    path: '/command-deck',
    accent: '#2563EB',
    accentDim: '#1E3A5F',
    accentGlow: 'rgba(37, 99, 235, 0.15)',
    gradient: 'radial-gradient(ellipse at 30% 15%, #0F1A3A 0%, transparent 65%), radial-gradient(ellipse at 70% 85%, #0A0F1A 0%, transparent 55%), radial-gradient(ellipse at 50% 50%, #0D1528 0%, transparent 70%)',
    lighting: {
      ambientColor: '#2563EB',
      ambientIntensity: 0.06,
      vignetteColor: '#000',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'All systems operational. Command Deck at full readiness.',
    olloWelcome: 'Welcome back to the Command Deck, Commander.',
    parentPaths: ['/dashboard', '/overview', '/notifications', '/command-deck'],
    particles: { density: 30, minSize: 2, maxSize: 5, speed: 6, driftX: 20, driftY: 15, behavior: 'drift' },
  },
  scanner: {
    id: 'scanner',
    name: 'Scanner Room',
    subtitle: 'Real-Time Asset Surveillance',
    path: '/scanner',
    accent: '#06B6D4',
    accentDim: '#0A3B40',
    accentGlow: 'rgba(6, 182, 212, 0.12)',
    gradient: 'radial-gradient(ellipse at 50% 0%, #0A2A30 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, #061A1F 0%, transparent 50%), radial-gradient(ellipse at 80% 50%, #0A1A20 0%, transparent 60%)',
    lighting: {
      ambientColor: '#06B6D4',
      ambientIntensity: 0.08,
      vignetteColor: '#061A1F',
      vignetteOpacity: 0.6,
      scanlineOpacity: 0.03,
    },
    olloMessage: 'Continuous scan active. All timeframes under surveillance.',
    olloWelcome: 'Scanner Room engaged. Analyzing market structure.',
    parentPaths: ['/scanner', '/asset'],
    particles: { density: 45, minSize: 1, maxSize: 2, speed: 3, driftX: 60, driftY: 5, behavior: 'scan' },
  },
  council: {
    id: 'ai-council',
    name: 'AI Council Chamber',
    subtitle: 'Multi-Agent Decision Chamber',
    path: '/decisions',
    accent: '#8B5CF6',
    accentDim: '#2A1A40',
    accentGlow: 'rgba(139, 92, 246, 0.12)',
    gradient: 'radial-gradient(ellipse at 40% 20%, #1A0A30 0%, transparent 60%), radial-gradient(ellipse at 60% 80%, #0F0A1A 0%, transparent 55%), radial-gradient(ellipse at 50% 50%, #150A24 0%, transparent 65%)',
    lighting: {
      ambientColor: '#8B5CF6',
      ambientIntensity: 0.07,
      vignetteColor: '#0F0A1A',
      vignetteOpacity: 0.55,
      scanlineOpacity: 0.025,
    },
    olloMessage: 'AI agents deliberating. Awaiting consensus signals.',
    olloWelcome: 'Entering the AI Council chamber. Agents are assembled.',
    parentPaths: ['/decisions', '/signals', '/intelligence', '/ai-experience', '/regime'],
    particles: { density: 25, minSize: 1, maxSize: 3, speed: 4, driftX: 8, driftY: -30, behavior: 'rise' },
  },
  riskRoom: {
    id: 'risk-room',
    name: 'Risk Operations',
    subtitle: 'Risk Metrics & Exposure',
    path: '/risk',
    accent: '#F43F5E',
    accentDim: '#3A0A14',
    accentGlow: 'rgba(244, 63, 94, 0.12)',
    gradient: 'radial-gradient(ellipse at 50% 20%, #2A0A14 0%, transparent 60%), radial-gradient(ellipse at 50% 80%, #1A060A 0%, transparent 55%)',
    lighting: {
      ambientColor: '#F43F5E',
      ambientIntensity: 0.09,
      vignetteColor: '#1A060A',
      vignetteOpacity: 0.6,
      scanlineOpacity: 0.025,
    },
    olloMessage: 'Risk metrics updated. All exposure limits monitored.',
    olloWelcome: 'Risk Operations active. Monitoring exposure and limits.',
    parentPaths: ['/risk'],
    particles: { density: 25, minSize: 2, maxSize: 4, speed: 5, driftX: 12, driftY: 18, behavior: 'drift' },
  },
  portfolio: {
    id: 'portfolio',
    name: 'Portfolio Vault',
    subtitle: 'Capital Allocation Center',
    path: '/portfolio',
    accent: '#3B82F6',
    accentDim: '#1A2E4A',
    accentGlow: 'rgba(59, 130, 246, 0.12)',
    gradient: 'radial-gradient(ellipse at 40% 10%, #112244 0%, transparent 60%), radial-gradient(ellipse at 70% 90%, #0A0F1A 0%, transparent 55%), radial-gradient(ellipse at 20% 50%, #0E1A2E 0%, transparent 60%)',
    lighting: {
      ambientColor: '#3B82F6',
      ambientIntensity: 0.06,
      vignetteColor: '#0A0F1A',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'Portfolio metrics updated. Performance overview ready.',
    olloWelcome: 'Portfolio Vault unlocked. Reviewing capital allocation.',
    parentPaths: ['/portfolio'],
    particles: { density: 35, minSize: 1, maxSize: 3, speed: 5, driftX: 15, driftY: 12, behavior: 'grid' },
  },
  whale: {
    id: 'whale',
    name: 'Whale Intelligence',
    subtitle: 'Deep Capital Flow Analysis',
    path: '/whale',
    accent: '#0E7490',
    accentDim: '#0A2E38',
    accentGlow: 'rgba(14, 116, 144, 0.12)',
    gradient: 'radial-gradient(ellipse at 60% 20%, #082A33 0%, transparent 60%), radial-gradient(ellipse at 30% 80%, #061A20 0%, transparent 55%), radial-gradient(ellipse at 80% 50%, #0A1A24 0%, transparent 60%)',
    lighting: {
      ambientColor: '#0E7490',
      ambientIntensity: 0.07,
      vignetteColor: '#061A20',
      vignetteOpacity: 0.55,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'Whale wallets synced. Large transactions being tracked.',
    olloWelcome: 'Descending into Whale Intelligence. Deep capital movements detected.',
    parentPaths: [],
    particles: { density: 20, minSize: 3, maxSize: 7, speed: 10, driftX: 10, driftY: 8, behavior: 'drift' },
  },
  missionArchive: {
    id: 'mission-archive',
    name: 'Mission Archive',
    subtitle: 'Trade Journal Archive',
    path: '/trades',
    accent: '#F59E0B',
    accentDim: '#3A2A0A',
    accentGlow: 'rgba(245, 158, 11, 0.12)',
    gradient: 'radial-gradient(ellipse at 30% 20%, #2A1F0A 0%, transparent 60%), radial-gradient(ellipse at 70% 80%, #1A140A 0%, transparent 55%), radial-gradient(ellipse at 50% 50%, #221A0A 0%, transparent 65%)',
    lighting: {
      ambientColor: '#F59E0B',
      ambientIntensity: 0.06,
      vignetteColor: '#1A140A',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.025,
    },
    olloMessage: 'Mission reports filed and archived for review.',
    olloWelcome: 'Opening the Mission Archive. All operations recorded.',
    parentPaths: ['/trades', '/timeline', '/journal'],
    particles: { density: 28, minSize: 1, maxSize: 3, speed: 7, driftX: 12, driftY: -10, behavior: 'ember' },
  },
  systemCore: {
    id: 'system-core',
    name: 'System Core',
    subtitle: 'AI Operations & Monitoring',
    path: '/analytics',
    accent: '#6366F1',
    accentDim: '#1A1A3A',
    accentGlow: 'rgba(99, 102, 241, 0.12)',
    gradient: 'radial-gradient(ellipse at 30% 20%, #14142E 0%, transparent 60%), radial-gradient(ellipse at 70% 80%, #0A0A1A 0%, transparent 55%)',
    lighting: {
      ambientColor: '#6366F1',
      ambientIntensity: 0.06,
      vignetteColor: '#0A0A1A',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'System core operational. All subsystems nominal.',
    olloWelcome: 'System Core initialized. AI operations online.',
    parentPaths: ['/analytics', '/backtest', '/hero-dashboard', '/profile', '/preferences'],
    particles: { density: 30, minSize: 1, maxSize: 3, speed: 5, driftX: 15, driftY: 25, behavior: 'grid' },
  },
  liquidity: {
    id: 'liquidity-lab',
    name: 'Liquidity Lab',
    subtitle: 'Order Book & Depth Analysis',
    path: '/funding',
    accent: '#10B981',
    accentDim: '#0A2E1A',
    accentGlow: 'rgba(16, 185, 129, 0.12)',
    gradient: 'radial-gradient(ellipse at 50% 20%, #0A2A18 0%, transparent 60%), radial-gradient(ellipse at 20% 80%, #061A0F 0%, transparent 55%), radial-gradient(ellipse at 80% 50%, #0A1A12 0%, transparent 60%)',
    lighting: {
      ambientColor: '#10B981',
      ambientIntensity: 0.06,
      vignetteColor: '#061A0F',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'Liquidity streams analyzed. Depth profiles updated.',
    olloWelcome: 'Liquidity Lab initialized. Flowing through order book data.',
    parentPaths: ['/funding', '/open-interest', '/liquidity'],
    particles: { density: 40, minSize: 1, maxSize: 3, speed: 4, driftX: 40, driftY: 10, behavior: 'flow' },
  },
  tradingFloor: {
    id: 'trading-floor',
    name: 'Trading Floor',
    subtitle: 'Execution & Order Management',
    path: '/execution',
    accent: '#14B8A6',
    accentDim: '#0A2E28',
    accentGlow: 'rgba(20, 184, 166, 0.12)',
    gradient: 'radial-gradient(ellipse at 50% 20%, #0A2824 0%, transparent 60%), radial-gradient(ellipse at 50% 80%, #061A16 0%, transparent 55%)',
    lighting: {
      ambientColor: '#14B8A6',
      ambientIntensity: 0.06,
      vignetteColor: '#061A16',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'Execution systems online. Orders flowing through the floor.',
    olloWelcome: 'Entering the Trading Floor. Execution systems active.',
    parentPaths: ['/execution', '/paper-trading', '/trading-workspace', '/trading-control'],
    particles: { density: 35, minSize: 1, maxSize: 4, speed: 4, driftX: 25, driftY: 20, behavior: 'flow' },
  },
  marketRoom: {
    id: 'market-room',
    name: 'Market Room',
    subtitle: 'Live Market Surveillance',
    path: '/market',
    accent: '#0EA5E9',
    accentDim: '#0A2A3A',
    accentGlow: 'rgba(14, 165, 233, 0.12)',
    gradient: 'radial-gradient(ellipse at 40% 10%, #0A1A2E 0%, transparent 60%), radial-gradient(ellipse at 60% 90%, #061A28 0%, transparent 55%)',
    lighting: {
      ambientColor: '#0EA5E9',
      ambientIntensity: 0.06,
      vignetteColor: '#061A28',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'Market feeds live. All pairs under surveillance.',
    olloWelcome: 'Market Room active. Streaming live data across all pairs.',
    parentPaths: ['/market', '/watchlists'],
    particles: { density: 40, minSize: 1, maxSize: 2, speed: 3, driftX: 35, driftY: 8, behavior: 'drift' },
  },
  default: {
    id: 'default',
    name: 'Command Deck',
    subtitle: 'Primary Operations Hub',
    path: '/',
    accent: '#2563EB',
    accentDim: '#1E3A5F',
    accentGlow: 'rgba(37, 99, 235, 0.15)',
    gradient: 'radial-gradient(ellipse at 30% 15%, #0F1A3A 0%, transparent 65%), radial-gradient(ellipse at 70% 85%, #0A0F1A 0%, transparent 55%), radial-gradient(ellipse at 50% 50%, #0D1528 0%, transparent 70%)',
    lighting: {
      ambientColor: '#2563EB',
      ambientIntensity: 0.06,
      vignetteColor: '#000',
      vignetteOpacity: 0.5,
      scanlineOpacity: 0.02,
    },
    olloMessage: 'All systems operational. Command Deck at full readiness.',
    olloWelcome: 'Welcome back, Commander. The headquarters is online.',
    parentPaths: [],
    particles: { density: 30, minSize: 2, maxSize: 5, speed: 6, driftX: 20, driftY: 15, behavior: 'drift' },
  },
};

export function getRoomForPath(pathname: string): RoomDefinition {
  const match = Object.values(ROOMS).find((r) =>
    r.parentPaths.some((p) => pathname.startsWith(p)),
  );
  return match ?? ROOMS.default;
}

export { ROOMS };
