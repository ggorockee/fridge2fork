/**
 * Components 데모 페이지
 * Linear 테마 시스템의 모든 컴포넌트를 확인할 수 있는 페이지
 */

"use client";

import React from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/Card";
import { Carousel } from "@/components/ui/Carousel";
import { Input } from "@/components/ui/Input";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/layout/Hero";
import { Container } from "@/components/layout/Container";
import { Grid, GridItem } from "@/components/layout/Grid";

export default function ComponentsPage() {
  // 데모용 데이터
  const menuItems = [
    {
      label: "홈",
      href: "/",
      active: true,
    },
    {
      label: "레시피",
      href: "/recipes",
      children: [
        { label: "전체 레시피", href: "/recipes" },
        { label: "인기 레시피", href: "/recipes/popular" },
        { label: "최신 레시피", href: "/recipes/latest" },
      ],
    },
    {
      label: "식재료",
      href: "/ingredients",
    },
    {
      label: "관리",
      href: "/admin",
    },
  ];

  const carouselItems = [
    <Card key={1} variant="default" hoverable>
      <CardContent>
        <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg mb-4 flex items-center justify-center">
          <span className="text-gray-400">이미지 1</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-100 mb-2">레시피 카드 1</h3>
        <p className="text-sm text-gray-400">맛있는 레시피 설명입니다.</p>
      </CardContent>
    </Card>,
    <Card key={2} variant="default" hoverable>
      <CardContent>
        <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg mb-4 flex items-center justify-center">
          <span className="text-gray-400">이미지 2</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-100 mb-2">레시피 카드 2</h3>
        <p className="text-sm text-gray-400">맛있는 레시피 설명입니다.</p>
      </CardContent>
    </Card>,
    <Card key={3} variant="default" hoverable>
      <CardContent>
        <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg mb-4 flex items-center justify-center">
          <span className="text-gray-400">이미지 3</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-100 mb-2">레시피 카드 3</h3>
        <p className="text-sm text-gray-400">맛있는 레시피 설명입니다.</p>
      </CardContent>
    </Card>,
    <Card key={4} variant="default" hoverable>
      <CardContent>
        <div className="h-48 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg mb-4 flex items-center justify-center">
          <span className="text-gray-400">이미지 4</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-100 mb-2">레시피 카드 4</h3>
        <p className="text-sm text-gray-400">맛있는 레시피 설명입니다.</p>
      </CardContent>
    </Card>,
  ];

  const footerSections = [
    {
      title: "서비스",
      links: [
        { label: "레시피 검색", href: "/recipes" },
        { label: "식재료 관리", href: "/ingredients" },
        { label: "즐겨찾기", href: "/favorites" },
        { label: "도움말", href: "/help" },
      ],
    },
    {
      title: "회사",
      links: [
        { label: "소개", href: "/about" },
        { label: "팀", href: "/team" },
        { label: "채용", href: "/careers" },
        { label: "연락처", href: "/contact" },
      ],
    },
    {
      title: "법적 고지",
      links: [
        { label: "이용약관", href: "/terms" },
        { label: "개인정보처리방침", href: "/privacy" },
        { label: "쿠키 정책", href: "/cookies" },
      ],
    },
  ];

  const socialLinks = [
    {
      name: "Twitter",
      href: "https://twitter.com",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
        </svg>
      ),
    },
    {
      name: "GitHub",
      href: "https://github.com",
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navbar */}
      <Navbar
        brand="Fridge2Fork"
        menuItems={menuItems}
        actions={
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              로그인
            </Button>
            <Button variant="primary" size="sm">
              시작하기
            </Button>
          </div>
        }
      />

      {/* Hero Section */}
      <Hero
        variant="centered"
        size="lg"
        title="컴포넌트 시스템"
        subtitle="Linear 테마 기반"
        description="Fridge2Fork Admin Web에서 사용하는 모든 컴포넌트를 확인하고 테스트할 수 있습니다."
        actions={[
          { label: "시작하기", variant: "primary" },
          { label: "문서 보기", variant: "secondary" },
        ]}
        stats={[
          { value: "15+", label: "컴포넌트" },
          { value: "3", label: "레이아웃" },
          { value: "100%", label: "접근성" },
        ]}
      />

      {/* Main Content */}
      <Container maxWidth="xl" padding="lg">
        {/* Button Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-semibold text-gray-100 mb-8">Button 컴포넌트</h2>
          <Grid cols={3} gap="lg">
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>Primary Button</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Button variant="primary" size="sm">Small</Button>
                    <Button variant="primary" size="md">Medium</Button>
                    <Button variant="primary" size="lg">Large</Button>
                  </div>
                </CardContent>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>Secondary Button</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Button variant="secondary" size="sm">Small</Button>
                    <Button variant="secondary" size="md">Medium</Button>
                    <Button variant="secondary" size="lg">Large</Button>
                  </div>
                </CardContent>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>Ghost Button</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Button variant="ghost" size="sm">Small</Button>
                    <Button variant="ghost" size="md">Medium</Button>
                    <Button variant="ghost" size="lg">Large</Button>
                  </div>
                </CardContent>
              </Card>
            </GridItem>
          </Grid>
        </section>

        {/* Card Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-semibold text-gray-100 mb-8">Card 컴포넌트</h2>
          <Grid cols={3} gap="lg">
            <GridItem>
              <Card variant="default" hoverable>
                <CardHeader>
                  <CardTitle>기본 카드</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400">
                    기본 스타일의 카드입니다. 호버 효과가 적용됩니다.
                  </p>
                </CardContent>
                <CardFooter>
                  <Button variant="primary" size="sm">액션</Button>
                </CardFooter>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="elevated" hoverable>
                <CardHeader>
                  <CardTitle>Elevated 카드</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400">
                    그림자가 있는 카드입니다. 더 높은 시각적 계층을 제공합니다.
                  </p>
                </CardContent>
                <CardFooter>
                  <Button variant="secondary" size="sm">액션</Button>
                </CardFooter>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="glass" hoverable>
                <CardHeader>
                  <CardTitle>Glass 카드</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400">
                    글래스모피즘 효과가 적용된 카드입니다.
                  </p>
                </CardContent>
                <CardFooter>
                  <Button variant="ghost" size="sm">액션</Button>
                </CardFooter>
              </Card>
            </GridItem>
          </Grid>
        </section>

        {/* Input Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-semibold text-gray-100 mb-8">Input 컴포넌트</h2>
          <Grid cols={2} gap="lg">
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>기본 입력 필드</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Input
                      label="이메일"
                      placeholder="이메일을 입력하세요"
                      type="email"
                      required
                    />
                    <Input
                      label="비밀번호"
                      placeholder="비밀번호를 입력하세요"
                      type="password"
                      required
                    />
                    <Input
                      label="검색"
                      placeholder="검색어를 입력하세요"
                      helperText="도움말 텍스트입니다"
                    />
                  </div>
                </CardContent>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>에러 상태</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Input
                      label="에러 필드"
                      placeholder="잘못된 입력"
                      error
                      errorMessage="이 필드는 필수입니다"
                    />
                    <Input
                      label="비활성화"
                      placeholder="비활성화된 필드"
                      disabled
                    />
                  </div>
                </CardContent>
              </Card>
            </GridItem>
          </Grid>
        </section>

        {/* Carousel Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-semibold text-gray-100 mb-8">Carousel 컴포넌트</h2>
          <Card variant="default">
            <CardContent>
              <Carousel
                items={carouselItems}
                autoPlay={true}
                showDots={true}
                showArrows={true}
                itemsToShow={3}
                itemsToScroll={1}
                height="400px"
              />
            </CardContent>
          </Card>
        </section>

        {/* Layout Components Section */}
        <section className="mb-16">
          <h2 className="text-3xl font-semibold text-gray-100 mb-8">레이아웃 컴포넌트</h2>
          <Grid cols={2} gap="lg">
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>Container</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Container maxWidth="sm" background="surface" border="default" rounded="md">
                      <p className="text-sm text-gray-400">Small Container</p>
                    </Container>
                    <Container maxWidth="md" background="elevated" border="default" rounded="md">
                      <p className="text-sm text-gray-400">Medium Container</p>
                    </Container>
                    <Container maxWidth="lg" background="glass" border="default" rounded="md">
                      <p className="text-sm text-gray-400">Large Container</p>
                    </Container>
                  </div>
                </CardContent>
              </Card>
            </GridItem>
            <GridItem>
              <Card variant="default">
                <CardHeader>
                  <CardTitle>Grid System</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Grid cols={3} gap="sm">
                      <GridItem>
                        <div className="bg-gray-700 p-2 rounded text-center text-xs text-gray-300">1</div>
                      </GridItem>
                      <GridItem>
                        <div className="bg-gray-700 p-2 rounded text-center text-xs text-gray-300">2</div>
                      </GridItem>
                      <GridItem>
                        <div className="bg-gray-700 p-2 rounded text-center text-xs text-gray-300">3</div>
                      </GridItem>
                    </Grid>
                    <Grid cols={2} gap="md">
                      <GridItem>
                        <div className="bg-gray-700 p-4 rounded text-center text-sm text-gray-300">50%</div>
                      </GridItem>
                      <GridItem>
                        <div className="bg-gray-700 p-4 rounded text-center text-sm text-gray-300">50%</div>
                      </GridItem>
                    </Grid>
                  </div>
                </CardContent>
              </Card>
            </GridItem>
          </Grid>
        </section>
      </Container>

      {/* Footer */}
      <Footer
        sections={footerSections}
        socialLinks={socialLinks}
        companyInfo={{
          name: "Fridge2Fork",
          description: "냉장고에서 포크까지, 오늘의냉장고 관리자용 웹 애플리케이션",
        }}
        newsletter={{
          title: "뉴스레터 구독",
          description: "최신 업데이트를 받아보세요",
          placeholder: "이메일 주소",
          buttonText: "구독하기",
          onSubmit: (email) => console.log("Newsletter subscription:", email),
        }}
      />
    </div>
  );
}
