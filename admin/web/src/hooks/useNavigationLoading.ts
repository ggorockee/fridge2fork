"use client";

import { useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

/**
 * 페이지 네비게이션 로딩 상태를 관리하는 훅
 * Next.js 15의 페이지 전환을 감지하여 로딩 상태를 제공
 */
export function useNavigationLoading() {
  const [isLoading, setIsLoading] = useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // 페이지 변경 감지 시 로딩 시작
    setIsLoading(true);

    // 짧은 딜레이 후 로딩 종료 (페이지 렌더링 완료를 위한 시간)
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 300);

    return () => clearTimeout(timer);
  }, [pathname, searchParams]);

  return isLoading;
}