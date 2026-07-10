export interface TimelineEventDTO {
  id: number;
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface TimelineResponseDTO {
  events: TimelineEventDTO[];
  total: number;
  offset: number;
  limit: number;
}
