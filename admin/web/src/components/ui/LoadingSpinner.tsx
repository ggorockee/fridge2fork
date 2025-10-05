import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * LoadingSpinner Component
 * 전역 로딩 스피너 - 페이지 전환 시 블러 배경과 함께 표시
 */

interface LoadingSpinnerProps {
  /**
   * 로딩 상태 표시 여부
   */
  isLoading?: boolean;
  /**
   * 로딩 메시지
   */
  message?: string;
  /**
   * 추가 className
   */
  className?: string;
}

export const LoadingSpinner = React.forwardRef<
  HTMLDivElement,
  LoadingSpinnerProps
>(({ isLoading = true, message = "로딩 중...", className }, ref) => {
  if (!isLoading) return null;

  return (
    <div
      ref={ref}
      className={cn(
        "fixed inset-0 z-50",
        "flex items-center justify-center",
        "bg-background/80 backdrop-blur-sm",
        "animate-in fade-in duration-200",
        className
      )}
    >
      <div className="flex flex-col items-center gap-4">
        {/* Spinner */}
        <div className="relative">
          <div className="w-16 h-16 border-4 border-muted rounded-full"></div>
          <div
            className="absolute top-0 left-0 w-16 h-16 border-4 border-t-transparent rounded-full animate-spin"
            style={{ borderColor: '#10b981', borderTopColor: 'transparent' }}
          ></div>
        </div>

        {/* Message */}
        {message && (
          <p className="text-sm text-muted-foreground animate-pulse">
            {message}
          </p>
        )}
      </div>
    </div>
  );
});

LoadingSpinner.displayName = "LoadingSpinner";

/**
 * 인라인 로딩 스피너 (페이지 내부용)
 */
interface InlineSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const InlineSpinner = React.forwardRef<
  HTMLDivElement,
  InlineSpinnerProps
>(({ size = "md", className }, ref) => {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-2",
    lg: "w-12 h-12 border-3",
  };

  return (
    <div
      ref={ref}
      className={cn("relative inline-block", className)}
      role="status"
      aria-label="로딩 중"
    >
      <div className="relative">
        <div
          className={cn(
            sizeClasses[size],
            "border-muted rounded-full"
          )}
        ></div>
        <div
          className={cn(
            sizeClasses[size],
            "absolute top-0 left-0 border-t-transparent rounded-full animate-spin"
          )}
          style={{ borderColor: '#10b981', borderTopColor: 'transparent' }}
        ></div>
      </div>
    </div>
  );
});

InlineSpinner.displayName = "InlineSpinner";