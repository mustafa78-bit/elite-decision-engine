import { apiFetch } from "./client";
import type { PortfolioSummaryDTO, PortfolioDistributionDTO, PortfolioPerformanceDTO, PortfolioRiskDTO, PortfolioFullDTO } from "../types/api/portfolio";

export function fetchPortfolioSummary(): Promise<PortfolioSummaryDTO> {
  return apiFetch("/portfolio/summary");
}

export function fetchPortfolioDistribution(): Promise<PortfolioDistributionDTO> {
  return apiFetch("/portfolio/distribution");
}

export function fetchPortfolioPerformance(): Promise<PortfolioPerformanceDTO> {
  return apiFetch("/portfolio/performance");
}

export function fetchPortfolioRisk(): Promise<PortfolioRiskDTO> {
  return apiFetch("/portfolio/risk");
}

export function fetchPortfolioFull(): Promise<PortfolioFullDTO> {
  return apiFetch("/portfolio/full");
}
