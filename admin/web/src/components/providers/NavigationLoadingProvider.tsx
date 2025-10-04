"use client";

import { Suspense } from "react";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { useNavigationLoading } from "@/hooks/useNavigationLoading";

/**
 * NavigationLoadingIndicator
 * useSearchParams를 사용하므로 Suspense로 감싸야 함
 */
function NavigationLoadingIndicator() {
  const isLoading = useNavigationLoading();
  return <LoadingSpinner isLoading={isLoading} message="페이지 로딩 중..." />;
}

/**
 * NavigationLoadingProvider
 * 페이지 전환 시 전역 로딩 스피너를 표시하는 Provider
 */
export function NavigationLoadingProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Suspense fallback={null}>
        <NavigationLoadingIndicator />
      </Suspense>
      {children}
    </>
  );
}