"use client";

import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { useNavigationLoading } from "@/hooks/useNavigationLoading";

/**
 * NavigationLoadingProvider
 * 페이지 전환 시 전역 로딩 스피너를 표시하는 Provider
 */
export function NavigationLoadingProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const isLoading = useNavigationLoading();

  return (
    <>
      <LoadingSpinner isLoading={isLoading} message="페이지 로딩 중..." />
      {children}
    </>
  );
}