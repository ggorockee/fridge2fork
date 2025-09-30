"use client";

import { useEffect, useState } from "react";
import { Container } from "@/components/layout/Container";
import { Grid } from "@/components/layout/Grid";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Tooltip } from "@/components/ui/Tooltip";
import { databaseApi } from "@/lib/api/services";
import type { DatabaseTable, DatabaseStats } from "@/types/api";
import { WarningIcon } from "@/components/ui/Icon";

/**
 * Database Management Page
 * API 연동 with async data fetching
 */
export default function DatabasePage() {
  const [tables, setTables] = useState<DatabaseTable[]>([]);
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDatabaseData();
  }, []);

  async function loadDatabaseData() {
    try {
      setLoading(true);
      setError(null);

      const [tablesData, statsData] = await Promise.all([
        databaseApi.getTables(),
        databaseApi.getStats(),
      ]);

      setTables(tablesData);
      setStats(statsData);
    } catch (err: any) {
      console.error("Database data load error:", err);
      setError(err.message || "데이터를 불러오는데 실패했습니다");
    } finally {
      setLoading(false);
    }
  }

  const filteredTables = tables.filter((table) =>
    table.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
              <Button onClick={loadDatabaseData}>다시 시도</Button>
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
            <h1 className="text-4xl font-bold mb-2">데이터베이스 관리</h1>
            <p className="text-muted-foreground">
              데이터베이스 테이블 및 데이터를 관리합니다
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadDatabaseData}>
              새로고침
            </Button>
            <Button variant="primary">데이터 정규화</Button>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <Grid cols={4} gap="md">
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground mb-1">
                  총 테이블 수
                </div>
                <div className="text-3xl font-bold">{stats.total_tables}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground mb-1">
                  총 레코드 수
                </div>
                <div className="text-3xl font-bold">
                  {stats.total_rows.toLocaleString()}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground mb-1">
                  데이터베이스 크기
                </div>
                <div className="text-3xl font-bold">
                  {stats.total_size_mb.toFixed(1)} MB
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground mb-1">
                  마지막 백업
                </div>
                <div className="text-3xl font-bold">{stats.last_backup}</div>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Search */}
        <Card>
          <CardContent className="pt-6">
            <Input
              placeholder="테이블 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </CardContent>
        </Card>

        {/* Tables List */}
        <Card>
          <CardHeader>
            <CardTitle>데이터베이스 테이블</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 font-medium">
                      테이블명
                    </th>
                    <th className="text-left py-3 px-4 font-medium">행 수</th>
                    <th className="text-left py-3 px-4 font-medium">크기</th>
                    <th className="text-left py-3 px-4 font-medium">
                      마지막 업데이트
                    </th>
                    <th className="text-left py-3 px-4 font-medium">상태</th>
                    <th className="text-left py-3 px-4 font-medium">작업</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTables.map((table) => (
                    <tr
                      key={table.name}
                      className="border-b border-border hover:bg-muted/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <span className="font-mono font-medium">
                          {table.name}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {table.row_count.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {table.size_mb.toFixed(2)} MB
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {table.last_updated || "N/A"}
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            table.status === "active" ? "success" : "default"
                          }
                          size="sm"
                        >
                          {table.status === "active" ? "정상" : "비활성"}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">
                            조회
                          </Button>
                          <Button variant="ghost" size="sm">
                            내보내기
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Database Operations */}
        <Grid cols={2} gap="lg">
          <Card>
            <CardHeader>
              <CardTitle>데이터 정규화</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                데이터 일관성을 유지하고 중복을 제거합니다
              </p>
              <div className="space-y-2">
                <Button variant="outline" fullWidth className="justify-start">
                  레시피 데이터 정규화
                </Button>
                <Button variant="outline" fullWidth className="justify-start">
                  재료 데이터 정규화
                </Button>
                <Button variant="outline" fullWidth className="justify-start">
                  사용자 데이터 정규화
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>백업 및 복원</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                데이터베이스 백업을 생성하거나 복원합니다
              </p>
              <div className="space-y-2">
                <Tooltip
                  content="지금은 사용할 수 없어요. 빠른 시일 내에 준비할게요"
                  disabled
                >
                  <Button variant="primary" fullWidth disabled>
                    전체 백업 생성
                  </Button>
                </Tooltip>
                <Tooltip
                  content="지금은 사용할 수 없어요. 빠른 시일 내에 준비할게요"
                  disabled
                >
                  <Button variant="outline" fullWidth disabled>
                    백업 목록 보기
                  </Button>
                </Tooltip>
                <Tooltip
                  content="지금은 사용할 수 없어요. 빠른 시일 내에 준비할게요"
                  disabled
                >
                  <Button variant="outline" fullWidth disabled>
                    백업 복원
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