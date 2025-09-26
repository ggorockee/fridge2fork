import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export default function Home() {
  // 네비게이션 메뉴 아이템들
  const menuItems = [
    {
      label: "대시보드",
      href: "/dashboard",
      active: true,
    },
    {
      label: "데이터 관리",
      href: "/data",
      children: [
        { label: "테이블 목록", href: "/data/tables" },
        { label: "레시피 데이터", href: "/data/recipes" },
        { label: "사용자 데이터", href: "/data/users" },
        { label: "식재료 데이터", href: "/data/ingredients" },
      ],
    },
    {
      label: "환경 관리",
      href: "/environments",
      children: [
        { label: "개발 환경", href: "/environments/dev" },
        { label: "운영 환경", href: "/environments/prod" },
        { label: "환경 전환", href: "/environments/switch" },
      ],
    },
    {
      label: "시스템",
      href: "/system",
      children: [
        { label: "감사 로그", href: "/system/audit-logs" },
        { label: "서비스 상태", href: "/system/status" },
        { label: "백업 관리", href: "/system/backup" },
      ],
    },
  ];

  // 액션 버튼들
  const actionButtons = (
    <div className="flex items-center space-x-2">
      <Button variant="ghost" size="sm">
        로그인
      </Button>
      <Button variant="primary" size="sm">
        관리자 접속
      </Button>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 네비게이션 바 */}
      <Navbar
        brand={
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">F2F</span>
            </div>
            <span className="text-xl font-semibold text-gray-100">Fridge2Fork</span>
          </div>
        }
        menuItems={menuItems}
        actions={actionButtons}
        glass={true}
        fixed={true}
      />

      {/* Hero 섹션 */}
      <section className="pt-24 pb-20 px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-100 mb-6 leading-tight">
              Fridge2Fork
              <br />
              <span className="bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
                관리자 패널
              </span>
            </h1>
            <p className="text-xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed">
              개발 및 운영 데이터베이스를 안전하게 조회하고 관리할 수 있는 
              웹 기반 관리자 시스템입니다. 
              k8s 환경에 직접 접근하지 않고도 데이터를 효율적으로 관리하세요.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button variant="primary" size="lg" className="px-8 py-4">
                관리자 로그인
              </Button>
              <Button variant="ghost" size="lg" className="px-8 py-4">
                시스템 상태 확인
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 기능 소개 섹션 */}
      <section className="py-20 px-8 bg-gray-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-4">
              데이터베이스 관리 기능
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              개발 및 운영 환경의 데이터베이스를 안전하게 조회하고 관리할 수 있는 
              전문적인 관리 도구를 제공합니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* 데이터 조회 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <CardTitle>데이터 조회</CardTitle>
                <CardDescription>
                  모든 테이블의 데이터를 페이지네이션과 필터링으로 안전하게 조회합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 테이블 목록 동적 조회</li>
                  <li>• 페이지네이션 지원</li>
                  <li>• 검색 및 필터링</li>
                  <li>• 환경별 데이터 분리</li>
                </ul>
              </CardContent>
            </Card>

            {/* 환경 관리 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <CardTitle>환경 관리</CardTitle>
                <CardDescription>
                  개발(dev)과 운영(prod) 환경을 분리하여 안전하게 관리합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 개발/운영 환경 분리</li>
                  <li>• 환경별 데이터 접근</li>
                  <li>• 환경 전환 기능</li>
                  <li>• 환경별 권한 관리</li>
                </ul>
              </CardContent>
            </Card>

            {/* 감사 로그 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <CardTitle>감사 로그</CardTitle>
                <CardDescription>
                  모든 데이터 변경 작업을 추적하고 기록하여 보안과 투명성을 보장합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 모든 변경 작업 기록</li>
                  <li>• 사용자별 활동 추적</li>
                  <li>• 변경 이력 조회</li>
                  <li>• 보안 감사 지원</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* 통계 섹션 */}
      <section className="py-20 px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-4">
              시스템 현황
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              현재 데이터베이스 상태와 관리자 활동 현황을 확인할 수 있습니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* 데이터베이스 테이블 수 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-orange-400 mb-2">15+</div>
                <div className="text-gray-400">관리 테이블</div>
              </CardContent>
            </Card>

            {/* 활성 관리자 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-green-400 mb-2">3</div>
                <div className="text-gray-400">활성 관리자</div>
              </CardContent>
            </Card>

            {/* 일일 작업 수 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-blue-400 mb-2">24</div>
                <div className="text-gray-400">일일 작업</div>
              </CardContent>
            </Card>

            {/* 시스템 가용성 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-purple-400 mb-2">99.9%</div>
                <div className="text-gray-400">시스템 가용성</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* 보안 안내 섹션 */}
      <section className="py-20 px-8 bg-gradient-to-r from-orange-500/10 to-orange-600/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-6">
            안전한 데이터 관리
          </h2>
          <p className="text-lg text-gray-400 mb-8 max-w-2xl mx-auto">
            JWT 기반 인증과 감사 로그를 통해 모든 데이터 접근과 변경 작업을 
            안전하게 추적하고 관리할 수 있습니다.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button variant="primary" size="lg" className="px-8 py-4">
              관리자 로그인
            </Button>
            <Button variant="ghost" size="lg" className="px-8 py-4">
              보안 정책 확인
            </Button>
          </div>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="py-12 px-8 bg-gray-800 border-t border-white/8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* 브랜드 */}
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">F2F</span>
                </div>
                <span className="text-xl font-semibold text-gray-100">Fridge2Fork</span>
              </div>
              <p className="text-gray-400 mb-4 max-w-md">
                개발 및 운영 데이터베이스를 안전하게 관리할 수 있는 
                전문적인 관리자 시스템입니다.
              </p>
            </div>

            {/* 빠른 링크 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-100 mb-4">빠른 링크</h3>
              <ul className="space-y-2">
                <li><a href="/dashboard" className="text-gray-400 hover:text-gray-100 transition-colors">대시보드</a></li>
                <li><a href="/data" className="text-gray-400 hover:text-gray-100 transition-colors">데이터 관리</a></li>
                <li><a href="/environments" className="text-gray-400 hover:text-gray-100 transition-colors">환경 관리</a></li>
                <li><a href="/system" className="text-gray-400 hover:text-gray-100 transition-colors">시스템 관리</a></li>
              </ul>
            </div>

            {/* 지원 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-100 mb-4">지원</h3>
              <ul className="space-y-2">
                <li><a href="/help" className="text-gray-400 hover:text-gray-100 transition-colors">도움말</a></li>
                <li><a href="/docs" className="text-gray-400 hover:text-gray-100 transition-colors">API 문서</a></li>
                <li><a href="/audit-logs" className="text-gray-400 hover:text-gray-100 transition-colors">감사 로그</a></li>
                <li><a href="/status" className="text-gray-400 hover:text-gray-100 transition-colors">시스템 상태</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/8 mt-8 pt-8 text-center">
            <p className="text-gray-400">
              © 2024 Fridge2Fork. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
