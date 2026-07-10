import { lazyLoad } from "../components/performance/lazy-load";

export const LazyHeroDashboard = lazyLoad(
  () => import("../pages/HeroDashboard"),
);

export const LazyTradingWorkspace = lazyLoad(
  () => import("../pages/TradingWorkspace"),
);

export const LazyAIExperience = lazyLoad(
  () => import("../pages/AIExperience"),
);

export const LazyProfessionalWorkspace = lazyLoad(
  () => import("../pages/ProfessionalWorkspace"),
);
