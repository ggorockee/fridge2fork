/**
 * Button 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 버튼 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * 버튼의 시각적 스타일 변형
   */
  variant?: "primary" | "secondary" | "ghost";
  /**
   * 버튼의 크기
   */
  size?: "sm" | "md" | "lg";
  /**
   * 로딩 상태
   */
  loading?: boolean;
  /**
   * 아이콘을 버튼 앞에 표시
   */
  leftIcon?: React.ReactNode;
  /**
   * 아이콘을 버튼 뒤에 표시
   */
  rightIcon?: React.ReactNode;
  /**
   * 전체 너비 사용 여부
   */
  fullWidth?: boolean;
  /**
   * 호버 효과 활성화 여부
   */
  hoverEffect?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      hoverEffect = true,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed";
    
    const variants = {
      primary: "bg-gray-100 text-gray-900 border border-gray-100 hover:bg-gray-200 hover:border-gray-200 focus:ring-gray-300",
      secondary: "bg-transparent text-gray-300 border-0 hover:text-gray-100 focus:ring-gray-300",
      ghost: "bg-transparent text-gray-300 border border-white/8 hover:bg-white/5 hover:text-gray-100 hover:border-white/12 focus:ring-gray-300",
    };
    
    const sizes = {
      sm: "px-3 py-2 text-xs rounded-md",
      md: "px-4 py-3 text-sm rounded-lg",
      lg: "px-6 py-4 text-base rounded-lg",
    };
    
    const hoverEffects = hoverEffect ? "hover:-translate-y-0.5" : "";
    
    return (
      <button
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          hoverEffects,
          fullWidth && "w-full",
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        
        {!loading && leftIcon && (
          <span className="mr-2 flex-shrink-0">{leftIcon}</span>
        )}
        
        {children && (
          <span className={cn(loading && "opacity-0")}>{children}</span>
        )}
        
        {!loading && rightIcon && (
          <span className="ml-2 flex-shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button };
