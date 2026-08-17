import { apiFetch } from "./client";

export interface CurrentUserDTO {
  id: number;
  username: string;
  email: string;
  created_at: string | null;
}

export function fetchCurrentUser(): Promise<CurrentUserDTO> {
  return apiFetch("/users/me");
}
