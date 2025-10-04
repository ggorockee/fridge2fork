/**
 * API Response Types
 */

// Dashboard Types
export interface DashboardStats {
  total_recipes: number;
  total_ingredients: number;
  total_recipe_ingredients: number;
  avg_ingredients_per_recipe: number;
}

// Raw API response from backend (한글 필드명)
export interface DashboardStatsRawResponse {
  data: {
    "총계": {
      "식재료": number;
      "레시피": number;
      "레시피-식재료 연결": number;
    };
    "식재료 분류": {
      "모호한 식재료": number;
      "정확한 식재료": number;
    };
    "평균값": {
      "레시피당 식재료 수": number;
      "식재료당 사용 횟수": number;
    };
    "최대값": {
      "가장 많이 사용된 식재료 사용 횟수": number;
      "가장 많은 식재료를 사용한 레시피의 식재료 수": number;
    };
  };
  metadata: {
    type: string;
    scope: string;
    calculation_method: string;
  };
  generated_at: string;
  cache_duration_seconds: number;
}

export interface DashboardOverview {
  stats: DashboardStats;
  recent_activities: Activity[];
  system_health: SystemHealth;
}

export interface Activity {
  id: number;
  action: string;
  user: string;
  timestamp: string;
  status: "success" | "error" | "warning" | "info";
  details?: string;
}

export interface SystemHealth {
  status: "healthy" | "warning" | "critical";
  database: {
    status: string;
    connection_pool: number;
    active_connections: number;
  };
  api: {
    status: string;
    response_time_ms: number;
  };
}

// Database Types
export interface DatabaseTable {
  name: string;
  row_count: number;
  size_mb: number;
  last_updated: string;
  status: "active" | "inactive";
}

// Raw API response for database tables
export interface DatabaseTableRaw {
  name: string;
  row_count: number;
  size: string; // "24 kB" 형식
  index_size: string;
  last_updated: string;
  status: "active" | "inactive";
  columns: Array<{
    name: string;
    type: string;
    nullable: boolean;
    primary_key?: boolean;
  }>;
}

export interface DatabaseTablesResponse {
  tables: DatabaseTableRaw[];
}

export interface DatabaseStats {
  total_tables: number;
  total_rows: number;
  total_size_mb: number;
  last_backup: string;
}

// System/Server Types
export interface SystemInfo {
  version: string;
  python_version: string;
  fastapi_version: string;
  database: {
    type: string;
    version: string;
  };
  uptime: string;
}

// Raw API response for system info
export interface SystemInfoRaw {
  status: string;
  uptime: string;
  version: string;
  environment: string;
  database: {
    status: string;
    version: string;
    tables_count: number;
  };
  server: {
    hostname: string;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export interface SystemResources {
  cpu: {
    usage_percent: number;
    cores: number;
  };
  memory: {
    usage_percent: number;
    total_mb: number;
    used_mb: number;
  };
  disk: {
    usage_percent: number;
    total_gb: number;
    used_gb: number;
  };
}

export interface ApiEndpoint {
  path: string;
  method: string;
  summary: string;
  tags: string[];
}

// Recipe Types
export interface Recipe {
  rcp_sno: number;
  rcp_nm: string;
  rcp_way2?: string;
  rcp_pat2?: string;
  info_wgt?: string;
  info_eng?: string;
  info_car?: string;
  info_pro?: string;
  info_fat?: string;
  info_na?: string;
  hash_tag?: string;
  att_file_no_main?: string;
  att_file_no_mk?: string;
  rcp_parts_dtls?: string;
  manual_img01?: string;
  manual01?: string;
  // ... 더 많은 manual 필드들
}

// Ingredient Types
export interface Ingredient {
  irdnt_sn: number;
  irdnt_nm: string;
  irdnt_ty_nm?: string;
  irdnt_ty_code?: string;
}

// Normalization Types
export interface NormalizationSuggestion {
  id: number;
  original_value: string;
  suggested_value: string;
  confidence_score: number;
  category: string;
  occurrences: number;
}

export interface NormalizationHistory {
  id: number;
  original_value: string;
  normalized_value: string;
  applied_at: string;
  applied_by: string;
  affected_recipes: number;
}

// Search Types
export interface SearchResult {
  type: "recipe" | "ingredient";
  id: number;
  name: string;
  category?: string;
  match_score: number;
}

// Pagination Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Common Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  status: number;
  message: string;
  originalError?: any;
}