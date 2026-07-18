import { useOutletContext } from "react-router-dom";

import type { LayoutContext } from "../components/layout/Layout";
import HeroBanner from "../components/dashboard/HeroBanner";
import AICouncilWidget from "../components/dashboard/AICouncilWidget";
import WhaleActivityCard from "../components/dashboard/WhaleActivityCard";

export default function Dashboard() {
  const { latestIntelligence } = useOutletContext<LayoutContext>();

  return (
    <div className="space-y-6">
      <div className="hero-enter">
        <HeroBanner />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="enter-1">
          <AICouncilWidget intelligence={latestIntelligence} />
        </div>
        <div className="enter-2">
          <WhaleActivityCard />
        </div>
      </div>
    </div>
  );
}
