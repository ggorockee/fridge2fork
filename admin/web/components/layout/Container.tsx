/**
 * Container 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 컨테이너 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * 컨테이너의 최대 너비
   */
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
  /**
   * 컨테이너의 패딩
   */
  padding?: "none" | "sm" | "md" | "lg" | "xl";
  /**
   * 컨테이너의 중앙 정렬 여부
   */
  centered?: boolean;
  /**
   * 컨테이너의 배경 스타일
   */
  background?: "transparent" | "surface" | "elevated" | "glass";
  /**
   * 컨테이너의 테두리 스타일
   */
  border?: "none" | "subtle" | "default" | "strong";
  /**
   * 컨테이너의 모서리 둥글기
   */
  rounded?: "none" | "sm" | "md" | "lg" | "xl";
}

const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  (
    {
      className,
      maxWidth = "xl",
      padding = "md",
      centered = true,
      background = "transparent",
      border = "none",
      rounded = "none",
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "w-full";
    
    const maxWidths = {
      sm: "max-w-2xl",
      md: "max-w-4xl",
      lg: "max-w-6xl",
      xl: "max-w-7xl",
      "2xl": "max-w-8xl",
      full: "max-w-full",
    };
    
    const paddings = {
      none: "p-0",
      sm: "p-4",
      md: "px-8 py-6",
      lg: "px-12 py-8",
      xl: "px-16 py-12",
    };
    
    const backgrounds = {
      transparent: "bg-transparent",
      surface: "bg-gray-800",
      elevated: "bg-gray-700",
      glass: "bg-white/5 backdrop-blur-xl",
    };
    
    const borders = {
      none: "border-0",
      subtle: "border border-white/8",
      default: "border border-white/12",
      strong: "border border-white/20",
    };
    
    const roundeds = {
      none: "rounded-none",
      sm: "rounded-sm",
      md: "rounded-md",
      lg: "rounded-lg",
      xl: "rounded-xl",
    };
    
    const marginStyles = centered ? "mx-auto" : "";
    
    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          maxWidths[maxWidth],
          paddings[padding],
          backgrounds[background],
          borders[border],
          roundeds[rounded],
          marginStyles,
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Container.displayName = "Container";

export { Container };
