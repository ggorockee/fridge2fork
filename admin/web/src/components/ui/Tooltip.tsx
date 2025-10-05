"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Tooltip Component
 * 마우스 호버 시 툴팁을 표시하는 컴포넌트
 */

interface TooltipProps {
  /**
   * 툴팁을 표시할 대상 요소
   */
  children: React.ReactNode;
  /**
   * 툴팁 내용
   */
  content: string;
  /**
   * 툴팁 위치
   */
  position?: "top" | "bottom" | "left" | "right";
  /**
   * 추가 className
   */
  className?: string;
  /**
   * 비활성화 상태 스타일 적용
   */
  disabled?: boolean;
}

export const Tooltip = React.forwardRef<HTMLDivElement, TooltipProps>(
  (
    { children, content, position = "top", className, disabled = false },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(false);

    const positionClasses = {
      top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
      bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
      left: "right-full top-1/2 -translate-y-1/2 mr-2",
      right: "left-full top-1/2 -translate-y-1/2 ml-2",
    };

    const arrowClasses = {
      top: "top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent",
      bottom:
        "bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent",
      left: "left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent",
      right:
        "right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent",
    };

    return (
      <div
        ref={ref}
        className={cn("relative inline-block", className)}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {/* Trigger element with disabled style */}
        <div className={cn(disabled && "opacity-50 cursor-not-allowed")}>
          {children}
        </div>

        {/* Tooltip */}
        {isVisible && content && (
          <div
            className={cn(
              "absolute z-50",
              "px-3 py-2",
              "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg",
              "text-sm text-gray-900 dark:text-gray-100",
              "whitespace-nowrap",
              "shadow-xl",
              "animate-in fade-in-0 zoom-in-95",
              "pointer-events-none",
              positionClasses[position]
            )}
            role="tooltip"
          >
            {content}

            {/* Arrow */}
            <div
              className={cn(
                "absolute",
                "w-0 h-0",
                "border-4 border-white dark:border-gray-900",
                arrowClasses[position]
              )}
            />
          </div>
        )}
      </div>
    );
  }
);

Tooltip.displayName = "Tooltip";