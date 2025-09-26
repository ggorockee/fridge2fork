/**
 * Card 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 카드 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";
import Image from "next/image";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * 카드의 시각적 스타일 변형
   */
  variant?: "default" | "elevated" | "outlined" | "glass";
  /**
   * 카드의 크기
   */
  size?: "sm" | "md" | "lg";
  /**
   * 호버 효과 활성화 여부
   */
  hoverable?: boolean;
  /**
   * 클릭 가능 여부
   */
  clickable?: boolean;
  /**
   * 카드 헤더
   */
  header?: React.ReactNode;
  /**
   * 카드 푸터
   */
  footer?: React.ReactNode;
  /**
   * 카드 이미지
   */
  image?: {
    src: string;
    alt: string;
    width?: number;
    height?: number;
    objectFit?: "cover" | "contain" | "fill" | "none" | "scale-down";
  };
  /**
   * 카드 제목
   */
  title?: string;
  /**
   * 카드 설명
   */
  description?: string;
  /**
   * 카드 액션 버튼들
   */
  actions?: React.ReactNode;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = "default",
      size = "md",
      hoverable = true,
      clickable = false,
      header,
      footer,
      image,
      title,
      description,
      actions,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "rounded-xl border transition-all duration-200";
    
    const variants = {
      default: "bg-gray-800 border-white/8",
      elevated: "bg-gray-800 border-white/8 shadow-lg",
      outlined: "bg-transparent border-white/12",
      glass: "bg-white/5 backdrop-blur-xl border-white/8",
    };
    
    const sizes = {
      sm: "p-4",
      md: "p-6",
      lg: "p-8",
    };
    
    const hoverStyles = hoverable ? "hover:bg-gray-700 hover:border-white/12 hover:-translate-y-1" : "";
    const clickableStyles = clickable ? "cursor-pointer" : "";
    
    return (
      <div
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          hoverStyles,
          clickableStyles,
          className
        )}
        ref={ref}
        {...props}
      >
        {/* 이미지 */}
        {image && (
          <div className="relative w-full mb-4 overflow-hidden rounded-lg">
            <Image
              src={image.src}
              alt={image.alt}
              width={image.width || 400}
              height={image.height || 200}
              className={cn(
                "w-full h-auto transition-transform duration-200",
                hoverable && "hover:scale-105"
              )}
              style={{ objectFit: image.objectFit || "cover" }}
            />
          </div>
        )}
        
        {/* 헤더 */}
        {header && (
          <div className="mb-4">
            {header}
          </div>
        )}
        
        {/* 제목 */}
        {title && (
          <h3 className="text-lg font-semibold text-gray-100 mb-2">
            {title}
          </h3>
        )}
        
        {/* 설명 */}
        {description && (
          <p className="text-sm text-gray-400 mb-4 leading-relaxed">
            {description}
          </p>
        )}
        
        {/* 콘텐츠 */}
        {children && (
          <div className="mb-4">
            {children}
          </div>
        )}
        
        {/* 액션 버튼들 */}
        {actions && (
          <div className="flex items-center justify-end gap-2 mt-4">
            {actions}
          </div>
        )}
        
        {/* 푸터 */}
        {footer && (
          <div className="mt-4 pt-4 border-t border-white/8">
            {footer}
          </div>
        )}
      </div>
    );
  }
);

Card.displayName = "Card";

// Card의 하위 컴포넌트들
export const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("text-lg font-semibold text-gray-100", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-gray-400", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("", className)} {...props} />
));
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center pt-4 border-t border-white/8", className)}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export { Card };
