import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Grid component for responsive layouts
 */
export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 6 | 12;
  gap?: "sm" | "md" | "lg" | "xl";
}

const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ className, cols = 3, gap = "md", ...props }, ref) => {
    const colsMap = {
      1: "grid-cols-1",
      2: "grid-cols-1 md:grid-cols-2",
      3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
      4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
      6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
      12: "grid-cols-12",
    };

    const gapMap = {
      sm: "gap-2",
      md: "gap-4",
      lg: "gap-6",
      xl: "gap-8",
    };

    return (
      <div
        ref={ref}
        className={cn("grid", colsMap[cols], gapMap[gap], className)}
        {...props}
      />
    );
  }
);

Grid.displayName = "Grid";

export { Grid };