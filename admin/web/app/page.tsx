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
      label: "레시피 관리",
      href: "/recipes",
      children: [
        { label: "레시피 목록", href: "/recipes/list" },
        { label: "레시피 추가", href: "/recipes/add" },
        { label: "카테고리 관리", href: "/recipes/categories" },
      ],
    },
    {
      label: "사용자 관리",
      href: "/users",
      children: [
        { label: "사용자 목록", href: "/users/list" },
        { label: "사용자 분석", href: "/users/analytics" },
      ],
    },
    {
      label: "시스템",
      href: "/system",
      children: [
        { label: "설정", href: "/system/settings" },
        { label: "로그", href: "/system/logs" },
        { label: "백업", href: "/system/backup" },
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
        관리자 시작하기
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
              냉장고에서 포크까지
              <br />
              <span className="bg-gradient-to-r from-orange-400 to-orange-600 bg-clip-text text-transparent">
                레시피 관리 시스템
              </span>
            </h1>
            <p className="text-xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed">
              오늘의냉장고 앱을 위한 강력한 관리자 웹사이트. 
              레시피 데이터베이스를 효율적으로 관리하고, 
              사용자 경험을 최적화하세요.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button variant="primary" size="lg" className="px-8 py-4">
                관리자 대시보드 시작하기
              </Button>
              <Button variant="ghost" size="lg" className="px-8 py-4">
                데모 보기
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
              강력한 관리 기능
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              레시피 추천 앱의 모든 데이터를 체계적으로 관리하고 분석할 수 있습니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* 레시피 관리 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <CardTitle>레시피 관리</CardTitle>
                <CardDescription>
                  20만개 이상의 레시피 데이터를 체계적으로 관리하고 분류합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 레시피 추가/수정/삭제</li>
                  <li>• 카테고리별 분류</li>
                  <li>• 재료 기반 검색</li>
                  <li>• 영양 정보 관리</li>
                </ul>
              </CardContent>
            </Card>

            {/* 사용자 분석 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <CardTitle>사용자 분석</CardTitle>
                <CardDescription>
                  사용자 행동 패턴을 분석하여 개인화된 추천을 제공합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 사용자 선호도 분석</li>
                  <li>• 레시피 조회 통계</li>
                  <li>• 검색 패턴 분석</li>
                  <li>• 개인화 추천 최적화</li>
                </ul>
              </CardContent>
            </Card>

            {/* 시스템 관리 */}
            <Card variant="glass" hoverable className="text-center">
              <CardHeader>
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <CardTitle>시스템 관리</CardTitle>
                <CardDescription>
                  안정적이고 확장 가능한 시스템 운영을 위한 관리 도구를 제공합니다.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm text-gray-400 space-y-2 text-left">
                  <li>• 실시간 모니터링</li>
                  <li>• 자동 백업 시스템</li>
                  <li>• 성능 최적화</li>
                  <li>• 보안 관리</li>
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
              플랫폼 현황
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              현재까지의 성과와 사용자 만족도를 확인해보세요.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* 레시피 수 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-orange-400 mb-2">200K+</div>
                <div className="text-gray-400">등록된 레시피</div>
              </CardContent>
            </Card>

            {/* 활성 사용자 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-green-400 mb-2">50K+</div>
                <div className="text-gray-400">활성 사용자</div>
              </CardContent>
            </Card>

            {/* 일일 조회수 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-blue-400 mb-2">1M+</div>
                <div className="text-gray-400">일일 조회수</div>
              </CardContent>
            </Card>

            {/* 만족도 */}
            <Card variant="elevated" className="text-center">
              <CardContent className="pt-6">
                <div className="text-4xl font-bold text-purple-400 mb-2">4.8★</div>
                <div className="text-gray-400">사용자 만족도</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA 섹션 */}
      <section className="py-20 px-8 bg-gradient-to-r from-orange-500/10 to-orange-600/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-100 mb-6">
            지금 시작하세요
          </h2>
          <p className="text-lg text-gray-400 mb-8 max-w-2xl mx-auto">
            Fridge2Fork 관리자 시스템으로 레시피 추천 앱을 더욱 효율적으로 운영해보세요.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button variant="primary" size="lg" className="px-8 py-4">
              무료로 시작하기
            </Button>
            <Button variant="ghost" size="lg" className="px-8 py-4">
              문의하기
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
                냉장고에서 포크까지, 오늘의냉장고 레시피 추천 앱을 위한 
                강력한 관리자 웹사이트입니다.
              </p>
            </div>

            {/* 빠른 링크 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-100 mb-4">빠른 링크</h3>
              <ul className="space-y-2">
                <li><a href="/dashboard" className="text-gray-400 hover:text-gray-100 transition-colors">대시보드</a></li>
                <li><a href="/recipes" className="text-gray-400 hover:text-gray-100 transition-colors">레시피 관리</a></li>
                <li><a href="/users" className="text-gray-400 hover:text-gray-100 transition-colors">사용자 관리</a></li>
                <li><a href="/system" className="text-gray-400 hover:text-gray-100 transition-colors">시스템 설정</a></li>
              </ul>
            </div>

            {/* 지원 */}
            <div>
              <h3 className="text-lg font-semibold text-gray-100 mb-4">지원</h3>
              <ul className="space-y-2">
                <li><a href="/help" className="text-gray-400 hover:text-gray-100 transition-colors">도움말</a></li>
                <li><a href="/docs" className="text-gray-400 hover:text-gray-100 transition-colors">문서</a></li>
                <li><a href="/contact" className="text-gray-400 hover:text-gray-100 transition-colors">문의하기</a></li>
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
