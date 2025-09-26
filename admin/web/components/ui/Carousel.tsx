/**
 * Carousel 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 캐러셀 컴포넌트
 */

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

export interface CarouselProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * 캐러셀 아이템들
   */
  items: React.ReactNode[];
  /**
   * 자동 재생 여부
   */
  autoPlay?: boolean;
  /**
   * 자동 재생 간격 (ms)
   */
  autoPlayInterval?: number;
  /**
   * 무한 루프 여부
   */
  infinite?: boolean;
  /**
   * 표시할 아이템 수
   */
  itemsToShow?: number;
  /**
   * 한 번에 스크롤할 아이템 수
   */
  itemsToScroll?: number;
  /**
   * 점 네비게이션 표시 여부
   */
  showDots?: boolean;
  /**
   * 화살표 네비게이션 표시 여부
   */
  showArrows?: boolean;
  /**
   * 캐러셀 높이
   */
  height?: string;
  /**
   * 아이템 간격
   */
  gap?: string;
}

const Carousel = React.forwardRef<HTMLDivElement, CarouselProps>(
  (
    {
      className,
      items,
      autoPlay = false,
      autoPlayInterval = 3000,
      infinite = true,
      itemsToShow = 1,
      itemsToScroll = 1,
      showDots = true,
      showArrows = true,
      height = "auto",
      gap = "16px",
      ...props
    },
    ref
  ) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isTransitioning, setIsTransitioning] = useState(false);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const carouselRef = useRef<HTMLDivElement>(null);

    // 자동 재생 로직
    useEffect(() => {
      if (autoPlay && items.length > itemsToShow) {
        intervalRef.current = setInterval(() => {
          setCurrentIndex((prev) => {
            if (prev >= items.length - itemsToShow) {
              return infinite ? 0 : prev;
            }
            return prev + itemsToScroll;
          });
        }, autoPlayInterval);
      }

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }, [autoPlay, autoPlayInterval, items.length, itemsToShow, itemsToScroll, infinite]);

    // 다음 슬라이드로 이동
    const goToNext = () => {
      if (isTransitioning) return;
      
      setIsTransitioning(true);
      setCurrentIndex((prev) => {
        if (prev >= items.length - itemsToShow) {
          return infinite ? 0 : prev;
        }
        return prev + itemsToScroll;
      });
      
      setTimeout(() => setIsTransitioning(false), 300);
    };

    // 이전 슬라이드로 이동
    const goToPrevious = () => {
      if (isTransitioning) return;
      
      setIsTransitioning(true);
      setCurrentIndex((prev) => {
        if (prev <= 0) {
          return infinite ? items.length - itemsToShow : prev;
        }
        return prev - itemsToScroll;
      });
      
      setTimeout(() => setIsTransitioning(false), 300);
    };

    // 특정 인덱스로 이동
    const goToSlide = (index: number) => {
      if (isTransitioning) return;
      
      setIsTransitioning(true);
      setCurrentIndex(index);
      setTimeout(() => setIsTransitioning(false), 300);
    };

    // 마우스 이벤트 핸들러
    const handleMouseEnter = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };

    const handleMouseLeave = () => {
      if (autoPlay && items.length > itemsToShow) {
        intervalRef.current = setInterval(() => {
          setCurrentIndex((prev) => {
            if (prev >= items.length - itemsToShow) {
              return infinite ? 0 : prev;
            }
            return prev + itemsToScroll;
          });
        }, autoPlayInterval);
      }
    };

    if (!items || items.length === 0) {
      return null;
    }

    return (
      <div
        ref={ref}
        className={cn("relative w-full", className)}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        {...props}
      >
        {/* 캐러셀 컨테이너 */}
        <div
          ref={carouselRef}
          className="overflow-hidden rounded-lg"
          style={{ height }}
        >
          <div
            className="flex transition-transform duration-300 ease-in-out"
            style={{
              transform: `translateX(-${currentIndex * (100 / itemsToShow)}%)`,
              gap,
            }}
          >
            {items.map((item, index) => (
              <div
                key={index}
                className="flex-shrink-0"
                style={{ width: `${100 / itemsToShow}%` }}
              >
                {item}
              </div>
            ))}
          </div>
        </div>

        {/* 화살표 네비게이션 */}
        {showArrows && items.length > itemsToShow && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-gray-800/80 backdrop-blur-sm border border-white/8 text-gray-300 hover:text-gray-100 hover:bg-gray-700/80 transition-all duration-200"
              disabled={!infinite && currentIndex === 0}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            
            <button
              onClick={goToNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-2 rounded-full bg-gray-800/80 backdrop-blur-sm border border-white/8 text-gray-300 hover:text-gray-100 hover:bg-gray-700/80 transition-all duration-200"
              disabled={!infinite && currentIndex >= items.length - itemsToShow}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </>
        )}

        {/* 점 네비게이션 */}
        {showDots && items.length > itemsToShow && (
          <div className="flex justify-center mt-4 space-x-2">
            {Array.from({ length: Math.ceil(items.length / itemsToShow) }).map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index * itemsToScroll)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-200",
                  currentIndex >= index * itemsToScroll && currentIndex < (index + 1) * itemsToScroll
                    ? "bg-gray-100"
                    : "bg-gray-600 hover:bg-gray-400"
                )}
              />
            ))}
          </div>
        )}
      </div>
    );
  }
);

Carousel.displayName = "Carousel";

export { Carousel };
