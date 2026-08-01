export interface WatchlistDTO {
  id: number;
  name: string;
  symbols: string[];
  created_at: string;
  updated_at: string;
}

export interface WatchlistCreateDTO {
  name: string;
  symbols?: string[];
}

export interface WatchlistUpdateDTO {
  name?: string;
  symbols?: string[];
}
