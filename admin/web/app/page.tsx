/**
 * 홈페이지 - 대시보드로 리다이렉트
 */

import { redirect } from 'next/navigation';

export default function Home() {
  // 홈페이지 접근 시 대시보드로 리다이렉트
  redirect('/dashboard');
}
