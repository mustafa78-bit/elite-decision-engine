export type ConnectionStatus = "CONNECTED" | "DISCONNECTED";

export interface WsRoomStatus {
  trades: ConnectionStatus;
  analytics: ConnectionStatus;
  portfolio: ConnectionStatus;
  notifications: ConnectionStatus;
  preferences: ConnectionStatus;
}
