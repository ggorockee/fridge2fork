"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { SvgIconProps } from "@mui/material";

/**
 * Material Icons imports
 * Each icon must be imported individually from @mui/icons-material
 */
// Dashboard & Navigation
export { default as RestaurantIcon } from "@mui/icons-material/Restaurant";
export { default as DashboardIcon } from "@mui/icons-material/Dashboard";
export { default as DatabaseIcon } from "@mui/icons-material/Storage";
export { default as ServerIcon } from "@mui/icons-material/DnsRounded";
export { default as RecipeIcon } from "@mui/icons-material/MenuBook";
export { default as SettingsIcon } from "@mui/icons-material/Settings";

// Actions
export { default as RefreshIcon } from "@mui/icons-material/Refresh";
export { default as WarningIcon } from "@mui/icons-material/Warning";
export { default as CheckIcon } from "@mui/icons-material/Check";
export { default as CloseIcon } from "@mui/icons-material/Close";
export { default as AddIcon } from "@mui/icons-material/Add";
export { default as RemoveIcon } from "@mui/icons-material/Remove";
export { default as EditIcon } from "@mui/icons-material/Edit";
export { default as DeleteIcon } from "@mui/icons-material/Delete";
export { default as SaveIcon } from "@mui/icons-material/Save";
export { default as CancelIcon } from "@mui/icons-material/Cancel";

// Data & Storage
export { default as FolderIcon } from "@mui/icons-material/FolderOpen";
export { default as FileIcon } from "@mui/icons-material/Description";
export { default as DownloadIcon } from "@mui/icons-material/CloudDownload";
export { default as UploadIcon } from "@mui/icons-material/CloudUpload";
export { default as BackupIcon } from "@mui/icons-material/Backup";
export { default as RestoreIcon } from "@mui/icons-material/RestoreFromTrash";

// Status & Feedback
export { default as SuccessIcon } from "@mui/icons-material/CheckCircle";
export { default as ErrorIcon } from "@mui/icons-material/Error";
export { default as InfoIcon } from "@mui/icons-material/Info";
export { default as WaitingIcon } from "@mui/icons-material/HourglassEmpty";
export { default as ProcessingIcon } from "@mui/icons-material/AutorenewRounded";

// System & Monitoring
export { default as ChartIcon } from "@mui/icons-material/BarChart";
export { default as TimelineIcon } from "@mui/icons-material/Timeline";
export { default as MemoryIcon } from "@mui/icons-material/Memory";
export { default as PerformanceIcon } from "@mui/icons-material/Speed";
export { default as DebugIcon } from "@mui/icons-material/BugReport";

// Search & Filter
export { default as SearchIcon } from "@mui/icons-material/Search";
export { default as FilterIcon } from "@mui/icons-material/FilterList";
export { default as SortIcon } from "@mui/icons-material/Sort";

// UI Elements
export { default as MoreIcon } from "@mui/icons-material/MoreVert";
export { default as ArrowForwardIcon } from "@mui/icons-material/ArrowForward";
export { default as ArrowBackIcon } from "@mui/icons-material/ArrowBack";
export { default as ExpandIcon } from "@mui/icons-material/ExpandMore";
export { default as CollapseIcon } from "@mui/icons-material/ExpandLess";

/**
 * Icon component props
 */
export interface IconProps extends SvgIconProps {
  /**
   * Size variant for the icon
   */
  size?: "sm" | "md" | "lg" | "xl";
}

/**
 * Base Icon component wrapper for consistent styling
 */
export const Icon = React.forwardRef<SVGSVGElement, IconProps>(
  ({ size = "md", className, ...props }, ref) => {
    const sizeClasses = {
      sm: "w-4 h-4 text-base",
      md: "w-5 h-5 text-lg",
      lg: "w-6 h-6 text-xl",
      xl: "w-8 h-8 text-2xl",
    };

    return (
      <span
        ref={ref as React.Ref<SVGSVGElement>}
        className={cn(
          "inline-flex items-center justify-center",
          sizeClasses[size],
          className
        )}
        {...props}
      />
    );
  }
);

Icon.displayName = "Icon";