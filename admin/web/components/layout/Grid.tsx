/**
 * Grid 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 그리드 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * 그리드의 열 수
   */
  cols?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  /**
   * 반응형 그리드 설정
   */
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    md?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    lg?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    xl?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  };
  /**
   * 그리드 아이템 간격
   */
  gap?: "none" | "sm" | "md" | "lg" | "xl";
  /**
   * 그리드 아이템 정렬
   */
  align?: "start" | "center" | "end" | "stretch";
  /**
   * 그리드 아이템 수직 정렬
   */
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
}

const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  (
    {
      className,
      cols = 1,
      responsive = {},
      gap = "md",
      align = "stretch",
      justify = "start",
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "grid";
    
    // 기본 열 수
    const colsClass = `grid-cols-${cols}`;
    
    // 반응형 열 수
    const responsiveClasses = Object.entries(responsive)
      .map(([breakpoint, cols]) => `${breakpoint}:grid-cols-${cols}`)
      .join(" ");
    
    // 간격
    const gaps = {
      none: "gap-0",
      sm: "gap-2",
      md: "gap-4",
      lg: "gap-6",
      xl: "gap-8",
    };
    
    // 정렬
    const aligns = {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
    };
    
    // 수직 정렬
    const justifies = {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
      evenly: "justify-evenly",
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          colsClass,
          responsiveClasses,
          gaps[gap],
          aligns[align],
          justifies[justify],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Grid.displayName = "Grid";

// Grid Item 컴포넌트
export interface GridItemProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * 그리드 아이템이 차지할 열 수
   */
  span?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  /**
   * 반응형 스팬 설정
   */
  responsive?: {
    sm?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    md?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    lg?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
    xl?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  };
  /**
   * 그리드 아이템 시작 위치
   */
  start?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  /**
   * 그리드 아이템 끝 위치
   */
  end?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
}

const GridItem = React.forwardRef<HTMLDivElement, GridItemProps>(
  (
    {
      className,
      span = 1,
      responsive = {},
      start,
      end,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "";
    
    // 기본 스팬
    const spanClass = `col-span-${span}`;
    
    // 반응형 스팬
    const responsiveClasses = Object.entries(responsive)
      .map(([breakpoint, span]) => `${breakpoint}:col-span-${span}`)
      .join(" ");
    
    // 시작 위치
    const startClass = start ? `col-start-${start}` : "";
    
    // 끝 위치
    const endClass = end ? `col-end-${end}` : "";
    
    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          spanClass,
          responsiveClasses,
          startClass,
          endClass,
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GridItem.displayName = "GridItem";

export { Grid, GridItem };
