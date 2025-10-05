import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Container component for consistent page layout
 */
export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, size = "xl", ...props }, ref) => {
    const sizes = {
      sm: "max-w-3xl",
      md: "max-w-5xl",
      lg: "max-w-7xl",
      xl: "max-w-[1400px]",
      full: "max-w-full",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "container mx-auto px-4 sm:px-6 lg:px-8",
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Container.displayName = "Container";

export { Container };