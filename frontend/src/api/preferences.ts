import { apiFetch } from "./client";
import type { UserPreferencesDTO, ThemeConfigDTO, LayoutConfigDTO } from "../types/api/preferences";

// The backend derives the current user from the auth token
// (api/routes/preferences.py's require_user_id(request), same convention
// as every other multi-tenancy-scoped route) and never reads a user_id
// query param -- these functions used to pass one (hardcoded to 1, always
// silently ignored server-side) left over from before that migration.

export function fetchPreferences(): Promise<UserPreferencesDTO> {
  return apiFetch("/preferences");
}

export function updatePreferences(data: Partial<UserPreferencesDTO>): Promise<UserPreferencesDTO> {
  return apiFetch("/preferences", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function updateTheme(theme = "dark"): Promise<UserPreferencesDTO> {
  return apiFetch(`/preferences/theme?theme=${theme}`, {
    method: "PUT",
  });
}

export function updateLayout(layout: Partial<LayoutConfigDTO>): Promise<UserPreferencesDTO> {
  return apiFetch("/preferences/layout", {
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
