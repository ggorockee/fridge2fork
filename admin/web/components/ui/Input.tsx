/**
 * Input 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 입력 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * 입력 필드의 시각적 스타일 변형
   */
  variant?: "default" | "outlined" | "filled" | "ghost";
  /**
   * 입력 필드의 크기
   */
  size?: "sm" | "md" | "lg";
  /**
   * 에러 상태
   */
  error?: boolean;
  /**
   * 에러 메시지
   */
  errorMessage?: string;
  /**
   * 라벨 텍스트
   */
  label?: string;
  /**
   * 도움말 텍스트
   */
  helperText?: string;
  /**
   * 왼쪽 아이콘
   */
  leftIcon?: React.ReactNode;
  /**
   * 오른쪽 아이콘
   */
  rightIcon?: React.ReactNode;
  /**
   * 전체 너비 사용 여부
   */
  fullWidth?: boolean;
  /**
   * 필수 입력 여부
   */
  required?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      error = false,
      errorMessage,
      label,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      required = false,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    
    const baseStyles = "w-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent";
    
    const variants = {
      default: "bg-white/5 border border-white/8 text-gray-100 placeholder-gray-400 focus:border-gray-300 focus:bg-white/8 focus:ring-gray-300",
      outlined: "bg-transparent border border-white/12 text-gray-100 placeholder-gray-400 focus:border-gray-300 focus:ring-gray-300",
      filled: "bg-gray-800 border border-transparent text-gray-100 placeholder-gray-400 focus:border-gray-300 focus:ring-gray-300",
      ghost: "bg-transparent border border-transparent text-gray-100 placeholder-gray-400 focus:border-gray-300 focus:ring-gray-300",
    };
    
    const sizes = {
      sm: "px-3 py-2 text-sm rounded-md",
      md: "px-4 py-3 text-sm rounded-lg",
      lg: "px-5 py-4 text-base rounded-lg",
    };
    
    const errorStyles = error
      ? "border-red-500 focus:border-red-500 focus:ring-red-500"
      : "";
    
    const iconPadding = leftIcon ? "pl-10" : "";
    const rightIconPadding = rightIcon ? "pr-10" : "";
    
    return (
      <div className={cn("space-y-2", fullWidth && "w-full")}>
        {/* 라벨 */}
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-100"
          >
            {label}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        
        {/* 입력 필드 컨테이너 */}
        <div className="relative">
          {/* 왼쪽 아이콘 */}
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}
          
          {/* 입력 필드 */}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              baseStyles,
              variants[variant],
              sizes[size],
              errorStyles,
              iconPadding,
              rightIconPadding,
              className
            )}
            {...props}
          />
          
          {/* 오른쪽 아이콘 */}
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {rightIcon}
            </div>
          )}
        </div>
        
        {/* 에러 메시지 */}
        {error && errorMessage && (
          <p className="text-sm text-red-500">{errorMessage}</p>
        )}
        
        {/* 도움말 텍스트 */}
        {!error && helperText && (
          <p className="text-sm text-gray-400">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
