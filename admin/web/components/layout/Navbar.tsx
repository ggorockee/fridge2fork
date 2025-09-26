/**
 * Navbar 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 네비게이션 바 컴포넌트
 */

"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

export interface NavbarProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * 로고 또는 브랜드 이름
   */
  brand?: React.ReactNode;
  /**
   * 네비게이션 메뉴 아이템들
   */
  menuItems?: Array<{
    label: string;
    href: string;
    active?: boolean;
    children?: Array<{
      label: string;
      href: string;
    }>;
  }>;
  /**
   * 오른쪽 액션 버튼들
   */
  actions?: React.ReactNode;
  /**
   * 스크롤 시 투명도 변경 여부
   */
  transparentOnScroll?: boolean;
  /**
   * 고정 위치 여부
   */
  fixed?: boolean;
  /**
   * 글래스모피즘 효과 적용 여부
   */
  glass?: boolean;
}

const Navbar = React.forwardRef<HTMLElement, NavbarProps>(
  (
    {
      className,
      brand,
      menuItems = [],
      actions,
      transparentOnScroll = true,
      fixed = true,
      glass = true,
      ...props
    },
    ref
  ) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isScrolled, setIsScrolled] = useState(false);

    // 스크롤 이벤트 핸들러
    React.useEffect(() => {
      if (!transparentOnScroll) return;

      const handleScroll = () => {
        setIsScrolled(window.scrollY > 20);
      };

      window.addEventListener("scroll", handleScroll);
      return () => window.removeEventListener("scroll", handleScroll);
    }, [transparentOnScroll]);

    const baseStyles = "w-full h-16 flex items-center justify-between px-8 transition-all duration-200";
    const positionStyles = fixed ? "fixed top-0 left-0 right-0 z-50" : "relative";
    const backgroundStyles = glass
      ? "backdrop-blur-xl border-b border-white/8"
      : "bg-gray-900 border-b border-white/8";
    const scrollStyles = transparentOnScroll && isScrolled
      ? "bg-gray-900/80"
      : "bg-transparent";

    return (
      <nav
        ref={ref}
        className={cn(
          baseStyles,
          positionStyles,
          backgroundStyles,
          scrollStyles,
          className
        )}
        {...props}
      >
        {/* 브랜드/로고 */}
        <div className="flex items-center">
          {brand || (
            <div className="text-xl font-semibold text-gray-100">
              Fridge2Fork
            </div>
          )}
        </div>

        {/* 데스크톱 메뉴 */}
        <div className="hidden md:flex items-center space-x-8">
          {menuItems.map((item, index) => (
            <div key={index} className="relative group">
              <a
                href={item.href}
                className={cn(
                  "text-sm font-medium transition-colors duration-200 hover:text-gray-100",
                  item.active ? "text-gray-100" : "text-gray-400"
                )}
              >
                {item.label}
              </a>
              
              {/* 드롭다운 메뉴 */}
              {item.children && item.children.length > 0 && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-white/8 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  <div className="py-2">
                    {item.children.map((child, childIndex) => (
                      <a
                        key={childIndex}
                        href={child.href}
                        className="block px-4 py-2 text-sm text-gray-300 hover:text-gray-100 hover:bg-gray-700 transition-colors duration-200"
                      >
                        {child.label}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 액션 버튼들 */}
        <div className="hidden md:flex items-center space-x-4">
          {actions || (
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="sm">
                로그인
              </Button>
              <Button variant="primary" size="sm">
                시작하기
              </Button>
            </div>
          )}
        </div>

        {/* 모바일 메뉴 버튼 */}
        <button
          className="md:hidden p-2 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition-colors duration-200"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isMenuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>

        {/* 모바일 메뉴 */}
        {isMenuOpen && (
          <div className="absolute top-full left-0 right-0 md:hidden bg-gray-900 border-b border-white/8 shadow-lg">
            <div className="px-8 py-4 space-y-4">
              {menuItems.map((item, index) => (
                <div key={index}>
                  <a
                    href={item.href}
                    className={cn(
                      "block text-sm font-medium transition-colors duration-200 hover:text-gray-100",
                      item.active ? "text-gray-100" : "text-gray-400"
                    )}
                  >
                    {item.label}
                  </a>
                  
                  {/* 모바일 드롭다운 메뉴 */}
                  {item.children && item.children.length > 0 && (
                    <div className="mt-2 ml-4 space-y-2">
                      {item.children.map((child, childIndex) => (
                        <a
                          key={childIndex}
                          href={child.href}
                          className="block text-sm text-gray-400 hover:text-gray-100 transition-colors duration-200"
                        >
                          {child.label}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {/* 모바일 액션 버튼들 */}
              <div className="pt-4 border-t border-white/8">
                <div className="flex flex-col space-y-2">
                  <Button variant="ghost" size="sm" fullWidth>
                    로그인
                  </Button>
                  <Button variant="primary" size="sm" fullWidth>
                    시작하기
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </nav>
    );
  }
);

Navbar.displayName = "Navbar";

export { Navbar };
