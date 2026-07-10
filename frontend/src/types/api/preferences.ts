export interface UserPreferencesDTO {
  theme: string;
  layout_config: LayoutConfigDTO;
  notification_preferences: Record<string, boolean>;
}

export interface ThemeConfigDTO {
  colors: Record<string, string>;
  fonts: Record<string, string>;
  spacing: Record<string, string>;
}

export interface LayoutConfigDTO {
  sidebar_collapsed?: boolean;
  widget_order?: string[];
}
