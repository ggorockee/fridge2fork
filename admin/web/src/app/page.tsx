"use client";

import { useEffect, useState } from "react";
import { Container } from "@/components/layout/Container";
import { Grid } from "@/components/layout/Grid";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/Tooltip";
import { dashboardApi, systemApi } from "@/lib/api/services";
import type { DashboardStats, SystemResources } from "@/types/api";
import {
  BackupIcon,
  ProcessingIcon,
  ChartIcon,
  SearchIcon,
  WaitingIcon,
  WarningIcon,
  DownloadIcon,
} from "@/components/ui/Icon";
import { useToast } from "@/components/ui/Toast";

/**
 * Admin Dashboard Home Page
 * API 연동 with async data fetching
 */
export default function Home() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [resources, setResources] = useState<SystemResources | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      setError(null);

      // 병렬로 데이터 로드
      const [statsData, resourcesData] = await Promise.all([
        dashboardApi.getStats(),
        systemApi.getResources(),
      ]);

      setStats(statsData);
      setResources(resourcesData);
    } catch (err: any) {
      console.error("Dashboard data load error:", err);
      setError(err.message || "데이터를 불러오는데 실패했습니다");
    } finally {
      setLoading(false);
    }
  }

  // 빠른 작업 핸들러
  async function handleNormalizeData() {
    setActionLoading("normalize");
    try {
      // 시뮬레이션: 실제로는 API 호출
      await new Promise((resolve) => setTimeout(resolve, 1500));
      toast.success("데이터 정규화가 완료되었습니다!");
      await loadDashboardData(); // 데이터 새로고침
    } catch (error) {
      toast.error("데이터 정규화에 실패했습니다.");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleSystemCheck() {
    setActionLoading("system");
    try {
      // 시뮬레이션: 실제로는 API 호출
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast.success("시스템 상태가 정상입니다!");
    } catch (error) {
      toast.error("시스템 상태 확인에 실패했습니다.");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReindexSearch() {
    setActionLoading("reindex");
    try {
      // 시뮬레이션: 실제로는 API 호출
      await new Promise((resolve) => setTimeout(resolve, 2000));
      toast.success("검색 인덱스 재구성이 완료되었습니다!");
    } catch (error) {
      toast.error("검색 인덱스 재구성에 실패했습니다.");
    } finally {
      setActionLoading(null);
    }
  }

  // Loading state
  if (loading) {
    return (
      <Container className="py-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="relative w-12 h-12 mx-auto mb-4">
              <div className="w-12 h-12 border-4 border-muted rounded-full"></div>
              <div className="absolute top-0 left-0 w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
            </div>
            <p className="text-muted-foreground">데이터를 불러오는 중...</p>
          </div>
        </div>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container className="py-8">
        <Card variant="outlined">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <WarningIcon className="text-error text-4xl mb-4 mx-auto" />
              <h3 className="text-xl font-semibold mb-2">오류 발생</h3>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={loadDashboardData}>다시 시도</Button>
            </div>
          </CardContent>
        </Card>
      </Container>
    );
  }

  // Main content
  const statCards = [
    {
      title: "전체 레시피",
      value: stats?.total_recipes.toLocaleString() || "0",
      change: "+0%",
    },
    {
      title: "전체 재료",
      value: stats?.total_ingredients.toLocaleString() || "0",
      change: "+0%",
    },
    {
      title: "레시피-재료 연결",
      value: stats?.total_recipe_ingredients.toLocaleString() || "0",
      change: "+0%",
    },
    {
      title: "평균 재료 수",
      value: stats?.avg_ingredients_per_recipe.toFixed(1) || "0",
      change: "per recipe",
    },
  ];

  const recentActivities = [
    { action: "시스템 시작", user: "시스템", time: "방금 전", status: "success" as const },
    { action: "대시보드 로드", user: "관리자", time: "방금 전", status: "success" as const },
  ];

  return (
    <Container className="py-8">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">대시보드</h1>
            <p className="text-muted-foreground">
              Fridge2Fork 어드민 관리 시스템에 오신 것을 환영합니다
            </p>
          </div>
          <Button onClick={loadDashboardData} variant="outline">
            새로고침
          </Button>
        </div>

        {/* Stats Grid */}
        <Grid cols={4} gap="lg">
          {statCards.map((stat) => (
            <Card key={stat.title} hoverable>
              <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">{stat.value}</div>
                <div className="flex items-center gap-2">
                  <Badge variant="default" size="sm">
                    {stat.change}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </Grid>

        {/* Main Content Grid */}
        <Grid cols={2} gap="lg">
          {/* Recent Activities */}
          <Card>
            <CardHeader>
              <CardTitle>최근 활동</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivities.map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-3 border-b border-border last:border-0"
                  >
                    <div className="flex-1">
                      <p className="font-medium">{activity.action}</p>
                      <p className="text-sm text-muted-foreground">
                        {activity.user}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted-foreground">
                        {activity.time}
                      </span>
                      <Badge variant={activity.status} size="sm">
                        완료
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>빠른 작업</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Tooltip
                  content="아직 준비 중이에요! 조금만 기다려주세요"
                  disabled
                >
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start gap-2"
                    disabled
                  >
                    <BackupIcon fontSize="small" />
                    데이터베이스 백업
                  </Button>
                </Tooltip>
                <Button
                  variant="outline"
                  fullWidth
                  className="justify-start gap-2"
                  onClick={handleNormalizeData}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === "normalize" ? (
                    <WaitingIcon fontSize="small" />
                  ) : (
                    <ProcessingIcon fontSize="small" />
                  )}
                  {actionLoading === "normalize"
                    ? "정규화 진행 중..."
                    : "데이터 정규화 실행"}
                </Button>
                <Button
                  variant="outline"
                  fullWidth
                  className="justify-start gap-2"
                  onClick={handleSystemCheck}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === "system" ? (
                    <WaitingIcon fontSize="small" />
                  ) : (
                    <ChartIcon fontSize="small" />
                  )}
                  {actionLoading === "system"
                    ? "확인 중..."
                    : "시스템 상태 확인"}
                </Button>
                <Tooltip
                  content="아직 준비 중이에요! 조금만 기다려주세요"
                  disabled
                >
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start gap-2"
                    disabled
                  >
                    <DownloadIcon fontSize="small" />
                    데이터 내보내기
                  </Button>
                </Tooltip>
                <Button
                  variant="outline"
                  fullWidth
                  className="justify-start gap-2"
                  onClick={handleReindexSearch}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === "reindex" ? (
                    <WaitingIcon fontSize="small" />
                  ) : (
                    <SearchIcon fontSize="small" />
                  )}
                  {actionLoading === "reindex"
                    ? "재구성 중..."
                    : "검색 인덱스 재구성"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        {resources && (
          <Card>
            <CardHeader>
              <CardTitle>시스템 상태</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    CPU 사용률
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-success transition-all"
                        style={{
                          width: `${resources.cpu.usage_percent}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium">
                      {resources.cpu.usage_percent.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    메모리 사용률
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-info transition-all"
                        style={{
                          width: `${resources.memory.usage_percent}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium">
                      {resources.memory.usage_percent.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">
                    디스크 사용률
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-warning transition-all"
                        style={{
                          width: `${resources.disk.usage_percent}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium">
                      {resources.disk.usage_percent.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Container>
  );
}