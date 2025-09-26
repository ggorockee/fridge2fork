/**
 * Footer 컴포넌트
 * Linear 테마에 맞춘 재사용 가능한 푸터 컴포넌트
 */

import React from "react";
import { cn } from "@/lib/utils";

export interface FooterProps extends React.HTMLAttributes<HTMLElement> {
  /**
   * 푸터의 시각적 스타일 변형
   */
  variant?: "default" | "minimal" | "glass";
  /**
   * 푸터 섹션들
   */
  sections?: Array<{
    title: string;
    links: Array<{
      label: string;
      href: string;
      external?: boolean;
    }>;
  }>;
  /**
   * 소셜 미디어 링크들
   */
  socialLinks?: Array<{
    name: string;
    href: string;
    icon: React.ReactNode;
  }>;
  /**
   * 저작권 정보
   */
  copyright?: string;
  /**
   * 회사 정보
   */
  companyInfo?: {
    name: string;
    description?: string;
    logo?: React.ReactNode;
  };
  /**
   * 뉴스레터 구독 섹션
   */
  newsletter?: {
    title: string;
    description: string;
    placeholder: string;
    buttonText: string;
    onSubmit: (email: string) => void;
  };
}

const Footer = React.forwardRef<HTMLElement, FooterProps>(
  (
    {
      className,
      variant = "default",
      sections = [],
      socialLinks = [],
      copyright = "© 2024 Fridge2Fork. All rights reserved.",
      companyInfo,
      newsletter,
      ...props
    },
    ref
  ) => {
    const baseStyles = "w-full border-t border-white/8";
    
    const variants = {
      default: "bg-gray-900",
      minimal: "bg-transparent",
      glass: "bg-white/5 backdrop-blur-xl",
    };
    
    const containerStyles = "max-w-7xl mx-auto px-8 py-16";
    
    return (
      <footer
        ref={ref}
        className={cn(baseStyles, variants[variant], className)}
        {...props}
      >
        <div className={containerStyles}>
          {/* 메인 콘텐츠 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
            {/* 회사 정보 */}
            {companyInfo && (
              <div className="lg:col-span-1">
                {companyInfo.logo || (
                  <div className="text-xl font-semibold text-gray-100 mb-4">
                    {companyInfo.name}
                  </div>
                )}
                {companyInfo.description && (
                  <p className="text-sm text-gray-400 leading-relaxed">
                    {companyInfo.description}
                  </p>
                )}
              </div>
            )}
            
            {/* 섹션들 */}
            {sections.map((section, index) => (
              <div key={index}>
                <h3 className="text-sm font-semibold text-gray-100 mb-4">
                  {section.title}
                </h3>
                <ul className="space-y-3">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a
                        href={link.href}
                        className="text-sm text-gray-400 hover:text-gray-100 transition-colors duration-200"
                        target={link.external ? "_blank" : undefined}
                        rel={link.external ? "noopener noreferrer" : undefined}
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            
            {/* 뉴스레터 구독 */}
            {newsletter && (
              <div>
                <h3 className="text-sm font-semibold text-gray-100 mb-4">
                  {newsletter.title}
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  {newsletter.description}
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.currentTarget);
                    const email = formData.get("email") as string;
                    newsletter.onSubmit(email);
                  }}
                  className="space-y-3"
                >
                  <input
                    type="email"
                    name="email"
                    placeholder={newsletter.placeholder}
                    className="w-full px-4 py-2 bg-white/5 border border-white/8 rounded-lg text-sm text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300 focus:border-transparent"
                    required
                  />
                  <button
                    type="submit"
                    className="w-full px-4 py-2 bg-gray-100 text-gray-900 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors duration-200"
                  >
                    {newsletter.buttonText}
                  </button>
                </form>
              </div>
            )}
          </div>
          
          {/* 하단 구분선 */}
          <div className="border-t border-white/8 pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
              {/* 저작권 정보 */}
              <div className="text-sm text-gray-400">
                {copyright}
              </div>
              
              {/* 소셜 미디어 링크들 */}
              {socialLinks.length > 0 && (
                <div className="flex items-center space-x-4">
                  {socialLinks.map((social, index) => (
                    <a
                      key={index}
                      href={social.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-gray-100 transition-colors duration-200"
                      aria-label={social.name}
                    >
                      {social.icon}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </footer>
    );
  }
);

Footer.displayName = "Footer";

export { Footer };
