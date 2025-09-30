"use client";

import { useEffect, useState } from "react";
import { Container } from "@/components/layout/Container";
import { Grid } from "@/components/layout/Grid";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/Tooltip";
import { systemApi } from "@/lib/api/services";
import type { SystemInfo, SystemResources } from "@/types/api";
import { WarningIcon } from "@/components/ui/Icon";

/**
 * Server Management Page
 * API 연동 with async data fetching
 */
export default function ServersPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [resources, setResources] = useState<SystemResources | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadServerData();

    // 10초마다 리소스 정보 갱신
    const interval = setInterval(() => {
      loadResources();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  async function loadServerData() {
    try {
      setLoading(true);
      setError(null);

      const [infoData, resourcesData] = await Promise.all([
        systemApi.getInfo(),
        systemApi.getResources(),
      ]);

      setSystemInfo(infoData);
      setResources(resourcesData);
    } catch (err: any) {
      console.error("Server data load error:", err);
      setError(err.message || "데이터를 불러오는데 실패했습니다");
    } finally {
      setLoading(false);
    }
  }

  async function loadResources() {
    try {
      const resourcesData = await systemApi.getResources();
      setResources(resourcesData);
    } catch (err) {
      console.error("Resources load error:", err);
    }
  }

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

  if (error) {
    return (
      <Container className="py-8">
        <Card variant="outlined">
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <WarningIcon className="text-error text-4xl mb-4 mx-auto" />
              <h3 className="text-xl font-semibold mb-2">오류 발생</h3>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={loadServerData}>다시 시도</Button>
            </div>
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Container className="py-8">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">서버 관리</h1>
            <p className="text-muted-foreground">
              애플리케이션 서버 상태를 모니터링하고 관리합니다
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadServerData}>
              새로고침
            </Button>
          </div>
        </div>

        {/* System Info */}
        {systemInfo && (
          <Card>
            <CardHeader>
              <CardTitle>시스템 정보</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">버전</p>
                  <p className="font-medium">{systemInfo.version}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    Python 버전
                  </p>
                  <p className="font-medium">{systemInfo.python_version}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    FastAPI 버전
                  </p>
                  <p className="font-medium">{systemInfo.fastapi_version}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">가동 시간</p>
                  <p className="font-medium">{systemInfo.uptime}</p>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground mb-1">데이터베이스</p>
                <p className="font-medium">
                  {systemInfo.database.type} {systemInfo.database.version}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Resource Usage */}
        {resources && (
          <Grid cols={3} gap="lg">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>CPU</span>
                  <Badge
                    variant={
                      (resources.cpu.usage_percent ?? 0) > 80
                        ? "error"
                        : (resources.cpu.usage_percent ?? 0) > 60
                        ? "warning"
                        : "success"
                    }
                    size="sm"
                  >
                    {(resources.cpu.usage_percent ?? 0).toFixed(1)}%
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">사용률</p>
                    <div className="h-4 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-info transition-all duration-500"
                        style={{
                          width: `${resources.cpu.usage_percent ?? 0}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">코어 수</p>
                    <p className="text-2xl font-bold">{resources.cpu.cores ?? 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>메모리</span>
                  <Badge
                    variant={
                      (resources.memory.usage_percent ?? 0) > 80
                        ? "error"
                        : (resources.memory.usage_percent ?? 0) > 60
                        ? "warning"
                        : "success"
                    }
                    size="sm"
                  >
                    {(resources.memory.usage_percent ?? 0).toFixed(1)}%
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">사용률</p>
                    <div className="h-4 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-warning transition-all duration-500"
                        style={{
                          width: `${resources.memory.usage_percent ?? 0}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">사용량</p>
                    <p className="text-2xl font-bold">
                      {(resources.memory.used_mb ?? 0).toFixed(0)} MB
                      <span className="text-sm text-muted-foreground font-normal">
                        {" "}
                        / {(resources.memory.total_mb ?? 0).toFixed(0)} MB
                      </span>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>디스크</span>
                  <Badge
                    variant={
                      (resources.disk.usage_percent ?? 0) > 80
                        ? "error"
                        : (resources.disk.usage_percent ?? 0) > 60
                        ? "warning"
                        : "success"
                    }
                    size="sm"
                  >
                    {(resources.disk.usage_percent ?? 0).toFixed(1)}%
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">사용률</p>
                    <div className="h-4 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-success transition-all duration-500"
                        style={{
                          width: `${resources.disk.usage_percent ?? 0}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">사용량</p>
                    <p className="text-2xl font-bold">
                      {(resources.disk.used_gb ?? 0).toFixed(1)} GB
                      <span className="text-sm text-muted-foreground font-normal">
                        {" "}
                        / {(resources.disk.total_gb ?? 0).toFixed(1)} GB
                      </span>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Server Actions */}
        <Grid cols={3} gap="lg">
          <Card>
            <CardHeader>
              <CardTitle>서버 제어</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    헬스체크 실행
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    성능 테스트
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    캐시 초기화
                  </Button>
                </Tooltip>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>모니터링</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    실시간 로그
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    성능 메트릭
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button
                    variant="outline"
                    fullWidth
                    className="justify-start"
                    disabled
                  >
                    에러 로그
                  </Button>
                </Tooltip>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>관리</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button variant="outline" fullWidth disabled>
                    API 문서
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button variant="outline" fullWidth disabled>
                    설정 관리
                  </Button>
                </Tooltip>
                <Tooltip content="이 기능은 아직 구현되지 않았습니다" disabled>
                  <Button variant="outline" fullWidth disabled>
                    백업 설정
                  </Button>
                </Tooltip>
              </div>
            </CardContent>
          </Card>
        </Grid>
      </div>
    </Container>
  );
}