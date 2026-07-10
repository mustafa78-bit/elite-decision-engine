import { apiFetch } from "./client";
import type { UserPreferencesDTO, ThemeConfigDTO, LayoutConfigDTO } from "../types/api/preferences";

export function fetchPreferences(userId = 1): Promise<UserPreferencesDTO> {
  return apiFetch(`/preferences?user_id=${userId}`);
}

export function updatePreferences(userId = 1, data: Partial<UserPreferencesDTO>): Promise<UserPreferencesDTO> {
  return apiFetch(`/preferences?user_id=${userId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function updateTheme(userId = 1, theme = "dark"): Promise<UserPreferencesDTO> {
  return apiFetch(`/preferences/theme?user_id=${userId}&theme=${theme}`, {
    method: "PUT",
  });
}

export function updateLayout(userId = 1, layout: Partial<LayoutConfigDTO>): Promise<UserPreferencesDTO> {
  return apiFetch(`/preferences/layout?user_id=${userId}`, {
    method: "PUT",
    body: JSON.stringify(layout),
  });
}

export function fetchThemeConfig(theme = "dark"): Promise<ThemeConfigDTO> {
  return apiFetch(`/preferences/theme-config?theme=${theme}`);
}

export function fetchDefaultPreferences(): Promise<UserPreferencesDTO> {
  return apiFetch("/preferences/defaults");
}
