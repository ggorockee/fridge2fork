/**
 * 관리자 대시보드 페이지
 * 시스템 상태, 데이터베이스 정보, 리소스 사용량 등 종합 모니터링
 */

"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// 시스템 정보 타입 정의
interface SystemInfo {
  status: 'healthy' | 'warning' | 'error';
  uptime: string;
  version: string;
  environment: 'development' | 'production';
}

interface DatabaseTable {
  name: string;
  rowCount: number;
  size: string;
  indexSize: string;
  lastUpdated: string;
  status: 'active' | 'inactive' | 'error';
}

interface ResourceUsage {
  cpu: number;
  memory: number;
  disk: number;
  network: {
    in: number;
    out: number;
  };
}

interface ApiEndpoint {
  path: string;
  method: string;
  status: 'up' | 'down' | 'slow';
  responseTime: number;
  lastChecked: string;
}

interface RecentActivity {
  id: string;
  type: 'create' | 'update' | 'delete' | 'error';
  table: string;
  user: string;
  timestamp: string;
  details: string;
}

export default function DashboardPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [databaseTables, setDatabaseTables] = useState<DatabaseTable[]>([]);
  const [resourceUsage, setResourceUsage] = useState<ResourceUsage | null>(null);
  const [apiEndpoints, setApiEndpoints] = useState<ApiEndpoint[]>([]);
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // 시스템 정보 조회
  const fetchSystemInfo = async () => {
    try {
      const healthData = await api.healthCheck();
      setSystemInfo({
        status: 'healthy',
        uptime: '7일 14시간 32분',
        version: '1.0.0',
        environment: 'development'
      });
    } catch (error) {
      setSystemInfo({
        status: 'error',
        uptime: '0일 0시간 0분',
        version: '1.0.0',
        environment: 'development'
      });
    }
  };

  // 데이터베이스 테이블 정보 조회
  const fetchDatabaseTables = async () => {
    // 실제 API가 없으므로 모의 데이터 사용
    const mockTables: DatabaseTable[] = [
      {
        name: 'recipes',
        rowCount: 200000,
        size: '2.4 GB',
        indexSize: '512 MB',
        lastUpdated: '2024-01-15 14:30:00',
        status: 'active'
      },
      {
        name: 'ingredients',
        rowCount: 15000,
        size: '45 MB',
        indexSize: '12 MB',
        lastUpdated: '2024-01-15 14:25:00',
        status: 'active'
      },
      {
        name: 'recipe_ingredients',
        rowCount: 850000,
        size: '1.8 GB',
        indexSize: '380 MB',
        lastUpdated: '2024-01-15 14:20:00',
        status: 'active'
      },
      {
        name: 'users',
        rowCount: 50000,
        size: '120 MB',
        indexSize: '35 MB',
        lastUpdated: '2024-01-15 14:15:00',
        status: 'active'
      },
      {
        name: 'user_preferences',
        rowCount: 25000,
        size: '28 MB',
        indexSize: '8 MB',
        lastUpdated: '2024-01-15 14:10:00',
        status: 'active'
      },
      {
        name: 'audit_logs',
        rowCount: 150000,
        size: '890 MB',
        indexSize: '200 MB',
        lastUpdated: '2024-01-15 14:05:00',
        status: 'active'
      }
    ];
    setDatabaseTables(mockTables);
  };

  // 리소스 사용량 조회
  const fetchResourceUsage = async () => {
    // 모의 데이터
    setResourceUsage({
      cpu: 45.2,
      memory: 68.7,
      disk: 78.3,
      network: {
        in: 125.6,
        out: 89.4
      }
    });
  };

  // API 엔드포인트 상태 조회
  const fetchApiEndpoints = async () => {
    const mockEndpoints: ApiEndpoint[] = [
      { path: '/health', method: 'GET', status: 'up', responseTime: 12, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/recipes/', method: 'GET', status: 'up', responseTime: 245, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/recipes/', method: 'POST', status: 'up', responseTime: 189, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/ingredients/', method: 'GET', status: 'up', responseTime: 156, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/ingredients/', method: 'POST', status: 'up', responseTime: 134, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/recipes/{id}', method: 'PUT', status: 'slow', responseTime: 1200, lastChecked: '2024-01-15 14:30:00' },
      { path: '/fridge2fork/v1/ingredients/{id}', method: 'DELETE', status: 'up', responseTime: 98, lastChecked: '2024-01-15 14:30:00' }
    ];
    setApiEndpoints(mockEndpoints);
  };

  // 최근 활동 조회
  const fetchRecentActivities = async () => {
    const mockActivities: RecentActivity[] = [
      { id: '1', type: 'create', table: 'recipes', user: 'admin', timestamp: '2024-01-15 14:28:00', details: '새 레시피 추가: 김치볶음밥' },
      { id: '2', type: 'update', table: 'ingredients', user: 'admin', timestamp: '2024-01-15 14:25:00', details: '식재료 정보 수정: 양파' },
      { id: '3', type: 'delete', table: 'recipes', user: 'admin', timestamp: '2024-01-15 14:22:00', details: '레시피 삭제: ID 18651' },
      { id: '4', type: 'create', table: 'ingredients', user: 'admin', timestamp: '2024-01-15 14:20:00', details: '새 식재료 추가: 브로콜리' },
      { id: '5', type: 'error', table: 'recipes', user: 'system', timestamp: '2024-01-15 14:18:00', details: 'API 호출 실패: 500 Internal Server Error' },
      { id: '6', type: 'update', table: 'users', user: 'admin', timestamp: '2024-01-15 14:15:00', details: '사용자 정보 업데이트: user_123' }
    ];
    setRecentActivities(mockActivities);
  };

  // 모든 데이터 조회
  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemInfo(),
        fetchDatabaseTables(),
        fetchResourceUsage(),
        fetchApiEndpoints(),
        fetchRecentActivities()
      ]);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('데이터 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 자동 새로고침
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000); // 30초마다 새로고침
    return () => clearInterval(interval);
  }, []);

  // 상태별 색상 반환
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'active':
      case 'up':
        return 'text-green-400';
      case 'warning':
      case 'slow':
        return 'text-yellow-400';
      case 'error':
      case 'down':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // 활동 타입별 색상 반환
  const getActivityColor = (type: string) => {
    switch (type) {
      case 'create':
        return 'text-green-400';
      case 'update':
        return 'text-blue-400';
      case 'delete':
        return 'text-red-400';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  // 네비게이션 메뉴
  const menuItems = [
    { label: "홈", href: "/", active: false },
    { label: "대시보드", href: "/dashboard", active: true },
    { label: "레시피 관리", href: "/recipes", active: false },
    { label: "식재료 관리", href: "/ingredients", active: false },
    { label: "시스템", href: "/system", active: false },
  ];

  const actionButtons = (
    <div className="flex items-center space-x-2">
      <Button variant="ghost" size="sm" onClick={fetchAllData} disabled={loading}>
        {loading ? "새로고침 중..." : "새로고침"}
      </Button>
      <Button variant="ghost" size="sm">
        로그아웃
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

      {/* 메인 콘텐츠 */}
      <div className="pt-24 px-8 pb-8">
        <div className="max-w-7xl mx-auto">
          {/* 헤더 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-100 mb-2">시스템 대시보드</h1>
            <p className="text-gray-400">
              마지막 업데이트: {lastUpdated.toLocaleString('ko-KR')}
            </p>
          </div>

          {/* 시스템 상태 카드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">시스템 상태</p>
                    <p className={cn("text-2xl font-bold", getStatusColor(systemInfo?.status || 'unknown'))}>
                      {systemInfo?.status === 'healthy' ? '정상' : 
                       systemInfo?.status === 'warning' ? '주의' : '오류'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                    <div className="w-6 h-6 bg-green-400 rounded-full"></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">가동 시간</p>
                    <p className="text-2xl font-bold text-gray-100">{systemInfo?.uptime || '0일 0시간 0분'}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">총 레시피 수</p>
                    <p className="text-2xl font-bold text-gray-100">
                      {databaseTables.find(t => t.name === 'recipes')?.rowCount.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">총 식재료 수</p>
                    <p className="text-2xl font-bold text-gray-100">
                      {databaseTables.find(t => t.name === 'ingredients')?.rowCount.toLocaleString() || '0'}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 리소스 사용량 */}
          {resourceUsage && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">CPU 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.cpu}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-blue-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.cpu}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">메모리 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.memory}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-green-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.memory}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">디스크 사용률</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-gray-100">{resourceUsage.disk}%</span>
                    <div className="w-16 h-16 relative">
                      <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-gray-700"
                          stroke="currentColor"
                          strokeWidth="3"
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                        <path
                          className="text-yellow-400"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${resourceUsage.disk}, 100`}
                          fill="none"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        />
                      </svg>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card variant="elevated">
                <CardHeader>
                  <CardTitle className="text-lg">네트워크</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">In</span>
                      <span className="text-sm text-gray-100">{resourceUsage.network.in} MB/s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-400">Out</span>
                      <span className="text-sm text-gray-100">{resourceUsage.network.out} MB/s</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 데이터베이스 테이블 정보 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>데이터베이스 테이블 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {databaseTables.map((table) => (
                    <div key={table.name} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-100">{table.name}</span>
                          <span className={cn("text-xs px-2 py-1 rounded", 
                            table.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          )}>
                            {table.status}
                          </span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          {table.rowCount.toLocaleString()} 행 • {table.size} • 인덱스: {table.indexSize}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          마지막 업데이트: {table.lastUpdated}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* API 엔드포인트 상태 */}
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>API 엔드포인트 상태</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {apiEndpoints.map((endpoint, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className={cn("text-xs px-2 py-1 rounded font-mono", 
                            endpoint.method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
                            endpoint.method === 'POST' ? 'bg-green-500/20 text-green-400' :
                            endpoint.method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-red-500/20 text-red-400'
                          )}>
                            {endpoint.method}
                          </span>
                          <span className="text-sm text-gray-100 font-mono">{endpoint.path}</span>
                        </div>
                        <div className="flex items-center gap-4 mt-1">
                          <span className={cn("text-xs", getStatusColor(endpoint.status))}>
                            {endpoint.status === 'up' ? '정상' : endpoint.status === 'slow' ? '느림' : '오류'}
                          </span>
                          <span className="text-xs text-gray-400">
                            {endpoint.responseTime}ms
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 최근 활동 */}
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>최근 활동</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentActivities.map((activity) => (
                  <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={cn("w-2 h-2 rounded-full", 
                        activity.type === 'create' ? 'bg-green-400' :
                        activity.type === 'update' ? 'bg-blue-400' :
                        activity.type === 'delete' ? 'bg-red-400' :
                        'bg-red-500'
                      )}></div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={cn("text-sm font-medium", getActivityColor(activity.type))}>
                            {activity.type === 'create' ? '생성' :
                             activity.type === 'update' ? '수정' :
                             activity.type === 'delete' ? '삭제' : '오류'}
                          </span>
                          <span className="text-sm text-gray-400">•</span>
                          <span className="text-sm text-gray-300">{activity.table}</span>
                          <span className="text-sm text-gray-400">•</span>
                          <span className="text-sm text-gray-400">{activity.user}</span>
                        </div>
                        <div className="text-sm text-gray-400 mt-1">{activity.details}</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">{activity.timestamp}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
