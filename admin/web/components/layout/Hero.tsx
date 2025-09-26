/**
 * Hero 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 히어로 섹션 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

export interface HeroProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * 히어로 섹션의 시각적 스타일 변형
   */
  variant?: "default" | "centered" | "split" | "minimal";
  /**
   * 히어로 섹션의 크기
   */
  size?: "sm" | "md" | "lg" | "xl";
  /**
   * 제목
   */
  title: string;
  /**
   * 부제목
   */
  subtitle?: string;
  /**
   * 설명 텍스트
   */
  description?: string;
  /**
   * 액션 버튼들
   */
  actions?: Array<{
    label: string;
    href?: string;
    onClick?: () => void;
    variant?: "primary" | "secondary" | "ghost";
    size?: "sm" | "md" | "lg";
  }>;
  /**
   * 배경 이미지
   */
  backgroundImage?: {
    src: string;
    alt: string;
    overlay?: boolean;
  };
  /**
   * 배경 그라디언트
   */
  backgroundGradient?: boolean;
  /**
   * 통계 정보
   */
  stats?: Array<{
    value: string;
    label: string;
  }>;
  /**
   * 추가 콘텐츠
   */
  children?: React.ReactNode;
}

const Hero = React.forwardRef<HTMLElement, HeroProps>(
  (
    {
      className,
      variant = "default",
      size = "lg",
      title,
      subtitle,
      description,
      actions = [],
      backgroundImage,
      backgroundGradient = false,
      stats = [],
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "relative w-full overflow-hidden";
    
    const variants = {
      default: "text-left",
      centered: "text-center",
      split: "text-left",
      minimal: "text-center",
    };
    
    const sizes = {
      sm: "py-16",
      md: "py-24",
      lg: "py-32",
      xl: "py-40",
    };
    
    const containerStyles = "max-w-7xl mx-auto px-8";
    
    return (
      <section
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {/* 배경 이미지 */}
        {backgroundImage && (
          <div className="absolute inset-0 z-0">
            <img
              src={backgroundImage.src}
              alt={backgroundImage.alt}
              className="w-full h-full object-cover"
            />
            {backgroundImage.overlay && (
              <div className="absolute inset-0 bg-black/50" />
            )}
          </div>
        )}
        
        {/* 배경 그라디언트 */}
        {backgroundGradient && (
          <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900" />
        )}
        
        {/* 콘텐츠 */}
        <div className={cn("relative z-10", containerStyles)}>
          <div className={cn(
            "grid gap-8",
            variant === "split" ? "lg:grid-cols-2 lg:items-center" : "grid-cols-1"
          )}>
            {/* 텍스트 콘텐츠 */}
            <div className={cn(
              "space-y-6",
              variant === "centered" && "text-center",
              variant === "minimal" && "text-center"
            )}>
              {/* 부제목 */}
              {subtitle && (
                <div className="text-sm font-medium text-gray-400 uppercase tracking-wide">
                  {subtitle}
                </div>
              )}
              
              {/* 제목 */}
              <h1 className={cn(
                "font-semibold text-gray-100 leading-tight",
                size === "sm" && "text-3xl md:text-4xl",
                size === "md" && "text-4xl md:text-5xl",
                size === "lg" && "text-5xl md:text-6xl",
                size === "xl" && "text-6xl md:text-7xl"
              )}>
                {title}
              </h1>
              
              {/* 설명 */}
              {description && (
                <p className={cn(
                  "text-gray-400 leading-relaxed",
                  size === "sm" && "text-base max-w-2xl",
                  size === "md" && "text-lg max-w-2xl",
                  size === "lg" && "text-xl max-w-3xl",
                  size === "xl" && "text-xl max-w-3xl",
                  (variant === "centered" || variant === "minimal") && "mx-auto"
                )}>
                  {description}
                </p>
              )}
              
              {/* 액션 버튼들 */}
              {actions.length > 0 && (
                <div className={cn(
                  "flex flex-wrap gap-4",
                  (variant === "centered" || variant === "minimal") && "justify-center"
                )}>
                  {actions.map((action, index) => (
                    <Button
                      key={index}
                      variant={action.variant || "primary"}
                      size={action.size || "md"}
                      onClick={action.onClick}
                      className="min-w-[120px]"
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              )}
              
              {/* 통계 정보 */}
              {stats.length > 0 && (
                <div className={cn(
                  "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 pt-8",
                  (variant === "centered" || variant === "minimal") && "max-w-4xl mx-auto"
                )}>
                  {stats.map((stat, index) => (
                    <div key={index} className="text-center">
                      <div className="text-2xl md:text-3xl font-bold text-gray-100 mb-2">
                        {stat.value}
                      </div>
                      <div className="text-sm text-gray-400">
                        {stat.label}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* 추가 콘텐츠 (split 레이아웃용) */}
            {variant === "split" && children && (
              <div className="lg:pl-8">
                {children}
              </div>
            )}
          </div>
          
          {/* 추가 콘텐츠 (기타 레이아웃용) */}
          {variant !== "split" && children && (
            <div className="mt-16">
              {children}
            </div>
          )}
        </div>
      </section>
    );
  }
);

Hero.displayName = "Hero";

export { Hero };
