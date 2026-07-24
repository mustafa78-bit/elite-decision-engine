export interface PortfolioSummaryDTO {
  total_pnl: number;
  total_trades: number;
  win_rate: number;
  avg_pnl: number;
  profit_factor: number;
  sharpe: number;
  max_drawdown: number;
  calmar: number;
  open_pnl: number;
  open_trades: number;
}

export interface PortfolioDistributionDTO {
  by_symbol: Record<string, number>;
  by_side: Record<string, number>;
  by_status: Record<string, number>;
}

export interface PortfolioPerformanceDTO {
  equity_curve: { time: string; value: number }[];
  monthly_returns: Record<string, number>;
  best_trade: number;
  worst_trade: number;
  avg_win: number;
  avg_loss: number;
}

export interface PortfolioRiskDTO {
  value_at_risk: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  max_drawdown: number;
  recovery_factor: number;
}

export interface SectorExposureDTO {
  sector: string;
  amount: number;
  percentage: number;
}

export interface CorrelationMatrixItemDTO {
  asset_a: string;
  asset_b: string;
  correlation: number;
}

export interface WorstCaseScenarioDTO {
  name: string;
  probability: string;
  description: string;
  estimated_loss: number;
  percentage_impact: number;
  critical_action: string;
}

export interface RebalancingSuggestionDTO {
  action: "TRIM" | "ALLOCATE";
  symbol: string;
  amount: number;
  percentage: number;
  reason: string;
  why?: string;
  evidence?: string;
  expected_benefit?: string;
}

export interface OpportunityRecommendationDTO {
  symbol: string;
  side: string;
  score: number;
  confidence: number;
  reason: string;
  why?: string;
  evidence?: string;
  expected_benefit?: string;
  actionable_link: string;
}

export interface PortfolioAdvisorExecutiveSummaryDTO {
  overall_health_score: number;
  current_risk_level: string;
  biggest_weakness: string;
  biggest_opportunity: string;
  recommended_action: string;
  conclusions: {
    health: string;
    diversification: string;
    stress_testing: string;
  };
}

export interface PortfolioAdvisorDTO {
  health_score: number;
  health_deductions: string[];
  executive_summary?: PortfolioAdvisorExecutiveSummaryDTO;
  diversification: {
    concentration_ratio: number;
    status: "DIVERSIFIED" | "MODERATE" | "CONCENTRATED";
    message: string;
  };
  sector_exposure: SectorExposureDTO[];
  correlation_matrix: CorrelationMatrixItemDTO[];
  risk: {
    score: number;
    label: string;
  };
  worst_case_scenarios: WorstCaseScenarioDTO[];
  rebalancing_suggestions: RebalancingSuggestionDTO[];
  opportunity_recommendations: OpportunityRecommendationDTO[];
}

export interface PortfolioFullDTO {
  summary: PortfolioSummaryDTO;
  distribution: PortfolioDistributionDTO;
  performance: PortfolioPerformanceDTO;
  risk: PortfolioRiskDTO;
  advisor?: PortfolioAdvisorDTO;
}
